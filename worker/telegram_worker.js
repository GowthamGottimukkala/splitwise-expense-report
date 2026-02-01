export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Only POST", { status: 405 });
    }

    const workerToken = request.headers.get("X-Worker-Token");
    if (workerToken && env.CLOUDFLARE_WORKER_TOKEN && workerToken === env.CLOUDFLARE_WORKER_TOKEN) {
      const payload = await request.json();
      if (payload?.type === "report" && payload.report && payload.chat_id) {
        await sendMessage(env, payload.chat_id, payload.report);
        return new Response("Report delivered", { status: 200 });
      }
      return new Response("Invalid payload", { status: 400 });
    }

    const update = await request.json();
    const message = update.message || update.edited_message;
    if (!message || !message.text) {
      return new Response("No message", { status: 200 });
    }

    const chatId = message.chat?.id;
    const username = message.from?.username;
    const text = message.text.trim();
    if (!chatId) {
      return new Response("No chat", { status: 200 });
    }

    if (env.TELEGRAM_ALLOWED_USERNAME && username !== env.TELEGRAM_ALLOWED_USERNAME) {
      await sendMessage(env, chatId, "Unauthorized user.");
      return new Response("Unauthorized", { status: 403 });
    }

    const [command, ...args] = text.split(/\s+/);
    if (command === "/help") {
      await sendMessage(
        env,
        chatId,
        "Commands:\n/report [args...] (forwarded to script)\n/help\nExample: /report --dated-after 2024-01-01 --dated-before 2024-01-31 --group-id 123456"
      );
      return new Response("Help", { status: 200 });
    }

    if (command !== "/report") {
      await sendMessage(env, chatId, "Use /report [args...] or /help");
      return new Response("Ignored", { status: 200 });
    }

    const forwardedArgs = args.join(" ");

    await sendMessage(env, chatId, "Running report... this can take a minute.");

    const payload = {
      ref: env.GH_REF || "main",
      inputs: {
        chat_id: String(chatId),
        args: forwardedArgs,
      },
    };

    const triggerResponse = await fetch(
      `https://api.github.com/repos/${env.GH_OWNER}/${env.GH_REPO}/actions/workflows/${env.GH_WORKFLOW_FILE}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GH_TOKEN}`,
          "User-Agent": "splitwise-telegram-bot",
          Accept: "application/vnd.github+json",
        },
        body: JSON.stringify(payload),
      }
    );

    if (!triggerResponse.ok) {
      const errorText = await triggerResponse.text();
      await sendMessage(env, chatId, `Failed to trigger workflow: ${errorText}`);
      return new Response("Trigger failed", { status: 500 });
    }

    await sendMessage(env, chatId, "Workflow triggered. You will receive the report here shortly.");
    return new Response("OK", { status: 200 });
  },
};

async function sendMessage(env, chatId, text) {
  const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text }),
  });
}

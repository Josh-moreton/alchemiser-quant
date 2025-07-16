
# Telegram Bot + GitHub Actions Integration

To link a Telegram bot with GitHub Actions, you essentially make the bot *call* GitHub’s API to trigger a workflow and then relay the results back to the user. The high-level steps are: create a Telegram bot, program it to show a button (via an inline keyboard) in chat, configure a GitHub workflow with a `workflow_dispatch` trigger, and write bot code that calls GitHub’s REST API. When the workflow completes, the bot can fetch its outputs and send them back via Telegram. Below is a step-by-step outline:

1. **Create a Telegram Bot (BotFather)**: On Telegram, chat with [@BotFather](https://t.me/BotFather) and use the `/newbot` command to create a new bot. Follow the prompts to pick a name and username. BotFather will give you a **token** (a long string) that authenticates your bot. Save this token securely (it’s like a password for your bot).

2. **Write bot code (e.g. in Python)**: Use a Telegram Bot library (e.g. [python-telegram-bot](https://python-telegram-bot.org/), Telebot, or even raw HTTP calls) with your BotFather token. Start by handling the `/start` command or similar to send an initial message. To add a button that triggers the action, use an *inline keyboard*: when sending a message, include a `reply_markup` with an `InlineKeyboardMarkup` object containing one or more `InlineKeyboardButton`s. For example, in Python you might do:

   ```python
   reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Run Bot", callback_data="run")]])
   bot.send_message(chat_id, "Press to run trading bot:", reply_markup=reply_markup)
   ```

   The Telegram API docs note that `reply_markup` can be an `InlineKeyboardMarkup` to attach buttons to your message. When the user taps the button, your bot will receive a callback query with `data="run"` (or whatever you set as `callback_data`).

3. **Handle the button callback**: In your bot’s code, set up a handler for callback queries. When you detect the user clicked the “Run Bot” button, your code should do the following:

   * *Acknowledge the callback* (to stop the loading spinner).
   * *Trigger the GitHub Action*. Use GitHub’s REST API to create a **workflow dispatch event**. Specifically, send a `POST` to:

     ```
     https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}.yml/dispatches
     ```

     Include JSON `{"ref": "main"}` (or your branch name) in the body, and an `Authorization: Bearer <TOKEN>` header where `<TOKEN>` is a GitHub Personal Access Token (PAT) with `repo` scope. GitHub’s docs show exactly this curl call example, which triggers a workflow run that you’ve configured to listen on `workflow_dispatch`. For example:

     ```bash
     curl -X POST -H "Authorization: Bearer $GH_TOKEN" \
          -H "Accept: application/vnd.github+json" \
          https://api.github.com/repos/your-username/your-repo/actions/workflows/run_bot.yml/dispatches \
          -d '{"ref":"main"}'
     ```

     (Be sure your `.github/workflows/run_bot.yml` has `on: workflow_dispatch` so it can be triggered manually.) After calling this endpoint, GitHub will immediately return a 204 status, meaning the run has been queued.

4. **Monitor and retrieve results**: After triggering, the GitHub workflow will run your Python trading bot. You can either have your Telegram bot poll GitHub or have the workflow push results. A simple approach: your bot code can poll the GitHub Actions API until the run completes. For example, use the [List workflow runs](https://docs.github.com/rest/actions/workflow-runs#list-workflow-runs-for-a-workflow) endpoint `GET /repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs` and filter by `event=workflow_dispatch`. Since your repo is public, GitHub allows *listing* runs without authentication (though the dispatch POST itself needs a token). Once you find the latest run (it will have a status like `in_progress` and then `completed`), check its `conclusion` (e.g. `success` or `failure`). You can then fetch logs or outputs. For example, you can use [Get a workflow run artifact](https://docs.github.com/rest/actions/artifacts#get-an-artifact) or [Get workflow run logs](https://docs.github.com/rest/actions/workflow-runs#get-workflow-run-logs) to download output files, or simply capture whatever your bot prints to console.

5. **Send output back via Telegram**: Once the workflow finishes, have your bot send a message (or file) to the Telegram chat with the results. You might format trading results or portfolio info as a text report and call `bot.send_message(chat_id, text)`. If the output is an image or large data (like a chart or a CSV), use `bot.send_photo` or `bot.send_document` with the file. The Telegram Bot API lets you send messages, photos, charts, etc. just like any normal bot message. This uses **Telegram’s infrastructure** (the Bot API) to deliver the content to the user – your code only needs to call the `sendMessage`, `sendPhoto`, etc. endpoints with the bot token.

6. **Make it public / hosting notes**: Keeping the GitHub repo public can simplify permissions – public repos allow your bot to poll run status without extra auth. Your Telegram bot itself can run on any server or even your PC; for development you can use “long polling” (the library handles it) without setting up a webhook. In production you might host the bot code on a cloud server or use a service that supports Telegram webhooks. All user interaction (button presses and message delivery) is handled by Telegram’s servers via the Bot API.

**Summary**: In summary, you create a Telegram bot (via BotFather) and write code (e.g. in Python) to send an inline button. When clicked, your code calls GitHub’s “workflow\_dispatch” API endpoint to start your trading bot workflow. After the workflow runs and produces output, your bot retrieves the results (using GitHub’s REST API) and sends them back to the user over Telegram. Key references: the [Telegram Bot API docs](https://core.telegram.org/bots/api) for buttons (`InlineKeyboardMarkup` via `reply_markup`), and GitHub’s REST docs for the workflow dispatch endpoint (plus note that public repos allow unauthenticated reads of run status).

**Sources:** Telegram’s official Bot API docs and tutorials, and GitHub’s REST API docs for Actions workflows.

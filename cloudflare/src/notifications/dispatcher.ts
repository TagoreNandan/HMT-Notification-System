import { DBQueries } from "../db/queries";
import { Env, NotificationEvent } from "../types";
import { sendEmailNotification } from "./email";
import { sendNtfyNotification } from "./ntfy";

export async function dispatchEvent(
  env: Env,
  db: DBQueries,
  event: NotificationEvent,
  userId: number = 7
): Promise<{ ntfySent: boolean; emailSent: boolean }> {
  let ntfySent = false;
  let emailSent = false;
  const nowIso = new Date().toISOString();

  // 1. ntfy Mobile Push
  if (env.NTFY_TOPIC) {
    const isLogged = await db.isNotificationLogged(
      event.event_id,
      userId,
      "ntfy",
      env.NTFY_TOPIC
    );

    if (!isLogged) {
      const success = await sendNtfyNotification(env, event);
      if (success) {
        const logged = await db.logNotificationAttempt(
          event.event_id,
          userId,
          "ntfy",
          env.NTFY_TOPIC,
          nowIso
        );
        if (logged) ntfySent = true;
      }
    } else {
      console.log(`ntfy push already sent for event ${event.event_id} (idempotent suppression)`);
    }
  }

  // 2. Resend Email
  if (env.RESEND_API_KEY && env.RESEND_TO_EMAIL) {
    const isLogged = await db.isNotificationLogged(
      event.event_id,
      userId,
      "email",
      env.RESEND_TO_EMAIL
    );

    if (!isLogged) {
      const success = await sendEmailNotification(env, event);
      if (success) {
        const logged = await db.logNotificationAttempt(
          event.event_id,
          userId,
          "email",
          env.RESEND_TO_EMAIL,
          nowIso
        );
        if (logged) emailSent = true;
      }
    } else {
      console.log(`Email alert already sent for event ${event.event_id} (idempotent suppression)`);
    }
  }

  return { ntfySent, emailSent };
}

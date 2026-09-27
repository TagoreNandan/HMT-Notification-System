import { Env, NotificationEvent } from "../types";

export async function sendEmailNotification(
  env: Env,
  event: NotificationEvent
): Promise<boolean> {
  if (!env.RESEND_API_KEY || !env.RESEND_TO_EMAIL) {
    console.log("Email notification skipped: RESEND_API_KEY or RESEND_TO_EMAIL not configured");
    return false;
  }

  const fromEmail = env.RESEND_FROM_EMAIL || "HMT Alert <onboarding@resend.dev>";
  const subject = formatSubject(event);
  const htmlContent = formatHtmlEmail(event);

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: fromEmail,
        to: [env.RESEND_TO_EMAIL],
        subject: subject,
        html: htmlContent,
      }),
    });

    if (!res.ok) {
      const errText = await res.text();
      console.error(`Resend Email API failed with HTTP ${res.status}: ${errText}`);
      return false;
    }

    console.log(`Email alert sent successfully via Resend for event ${event.event_id}`);
    return true;
  } catch (err) {
    console.error(`Email dispatch error for event ${event.event_id}:`, err);
    return false;
  }
}

function formatSubject(event: NotificationEvent): string {
  const priceStr = event.price ? ` - ₹${event.price.toLocaleString("en-IN")}` : "";
  if (event.event_type === "back_in_stock") {
    return `🚨 BACK IN STOCK: ${event.title}${priceStr}`;
  }
  if (event.event_type === "new_model") {
    return `✨ NEW MODEL DISCOVERED: ${event.title}${priceStr}`;
  }
  if (event.event_type === "price_change") {
    return `🏷️ PRICE CHANGE: ${event.title}${priceStr}`;
  }
  return `📢 HMT WATCH ALERT: ${event.title}`;
}

function formatHtmlEmail(event: NotificationEvent): string {
  const priceFormatted = event.price !== null && event.price !== undefined
    ? `₹${event.price.toLocaleString("en-IN")}`
    : "Price N/A";

  const stockBadge = event.in_stock
    ? `<span style="background-color: #10B981; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 14px;">IN STOCK</span>`
    : `<span style="background-color: #EF4444; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 14px;">OUT OF STOCK</span>`;

  const imageBlock = event.image_url
    ? `<div style="text-align: center; margin-bottom: 20px;">
        <img src="${event.image_url}" alt="${event.title}" style="max-width: 100%; max-height: 250px; border-radius: 8px; object-fit: contain;" />
       </div>`
    : "";

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>${event.title}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px;">
      <div style="max-width: 500px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; border: 1px solid #334155; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 20px;">
          <h2 style="margin: 0; color: #38bdf8; font-size: 20px;">⌚ HMT Watch Monitor</h2>
          ${stockBadge}
        </div>
        ${imageBlock}
        <h1 style="font-size: 22px; margin: 0 0 8px 0; color: #ffffff;">${event.title}</h1>
        <p style="color: #94a3b8; margin: 0 0 16px 0; font-size: 14px;">Source: <strong>${event.site_name}</strong> ${event.collection ? `| Collection: <strong>${event.collection}</strong>` : ""}</p>
        <div style="background-color: #0f172a; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
          <div style="font-size: 24px; font-weight: bold; color: #34d399;">${priceFormatted}</div>
          <div style="color: #64748b; font-size: 12px; margin-top: 4px;">Detected at: ${new Date(event.occurred_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}</div>
        </div>
        <div style="text-align: center;">
          <a href="${event.url}" style="display: inline-block; background-color: #0284c7; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: bold; font-size: 16px;">View Watch on HMT →</a>
        </div>
      </div>
    </body>
    </html>
  `;
}

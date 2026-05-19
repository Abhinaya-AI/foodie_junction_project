from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email, otp_code, user_name=''):
    subject = f"🍕 Your Foodie Junction OTP: {otp_code}"
    html_message = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.1)">
      <div style="background:linear-gradient(135deg,#FF6B35,#F7931E);padding:32px;text-align:center">
        <div style="color:#fff;font-size:26px;font-weight:800">🍔 Foodie Junction</div>
      </div>
      <div style="padding:40px 32px">
        <h2 style="color:#1a1a1a">{'Hi ' + user_name + '! 👋' if user_name else 'Hello! 👋'}</h2>
        <p style="color:#555">Your OTP is valid for <strong>10 minutes</strong>.</p>
        <div style="background:#FFF5EF;border:2px dashed #FF6B35;border-radius:12px;padding:24px;text-align:center;margin:24px 0">
          <div style="font-size:42px;font-weight:900;color:#FF6B35;letter-spacing:10px;font-family:monospace">{otp_code}</div>
          <div style="color:#888;font-size:13px;margin-top:8px">One-Time Password</div>
        </div>
        <p style="color:#dc3545;font-size:13px">⚠️ Do not share this OTP with anyone.</p>
      </div>
    </div>"""
    plain = f"Your Foodie Junction OTP is: {otp_code}  (valid 10 min)"
    try:
        send_mail(subject, plain, settings.DEFAULT_FROM_EMAIL, [email],
                  html_message=html_message, fail_silently=False)
    except Exception as e:
        # In dev, print OTP to console
        print(f"\n{'='*40}\n📧 OTP for {email}: {otp_code}\n{'='*40}\n")


def send_order_confirmation_email(order):
    subject = f"✅ Order #FJ{order.id:04d} Confirmed - Foodie Junction"
    rows = ''.join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{i.food_item.name}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:center'>{i.quantity}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:right'>₹{i.subtotal}</td></tr>"
        for i in order.items.all()
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto">
      <div style="background:linear-gradient(135deg,#FF6B35,#F7931E);padding:24px;text-align:center;border-radius:12px 12px 0 0">
        <div style="color:#fff;font-size:22px;font-weight:800">🍔 Foodie Junction</div>
      </div>
      <div style="padding:28px;background:#fff;border-radius:0 0 12px 12px;box-shadow:0 4px 16px rgba(0,0,0,.08)">
        <h2 style="color:#2d7a2d">✅ Order Confirmed!</h2>
        <p>Hi <b>{order.delivery_name}</b>, your order from <b>{order.restaurant.name}</b> is confirmed.</p>
        <div style="background:#f9f9f9;border-radius:8px;padding:14px;margin:16px 0">
          <b>Order #FJ{order.id:04d}</b> · Estimated delivery: 30–45 minutes
        </div>
        <table style="width:100%;border-collapse:collapse">
          <tr style="background:#FF6B35;color:#fff">
            <th style="padding:10px;text-align:left">Item</th>
            <th style="padding:10px;text-align:center">Qty</th>
            <th style="padding:10px;text-align:right">Price</th>
          </tr>
          {rows}
          <tr><td colspan="2" style="padding:10px;text-align:right;font-weight:700">Total</td>
          <td style="padding:10px;text-align:right;font-weight:700;color:#FF6B35">₹{order.total_amount}</td></tr>
        </table>
        <div style="margin-top:16px;padding:14px;background:#FFF5EF;border-radius:8px">
          <b>Delivering to:</b> {order.delivery_address}, {order.delivery_pincode}
        </div>
      </div>
    </div>"""
    try:
        send_mail(subject, f"Order #FJ{order.id:04d} confirmed. Total: ₹{order.total_amount}",
                  settings.DEFAULT_FROM_EMAIL, [order.user.email], html_message=html, fail_silently=True)
    except Exception as e:
        print(f"Email error: {e}")
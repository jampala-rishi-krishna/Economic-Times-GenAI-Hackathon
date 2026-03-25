import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sender_email = str(os.getenv("GMAIL_ADDRESS") or "")
        self.app_password = str(os.getenv("GMAIL_APP_PASSWORD") or "")
        self.enabled = bool(self.sender_email and self.app_password)

    def _get_base_html(self, content):
        """Professional NEXUS HTML email template - Gmail compatible with white background."""
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
                    background-color: #f5f5f5;
                    color: #1a1a1a;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .header {{
                    background-color: #2563eb;
                    padding: 24px;
                    color: #ffffff;
                }}
                .header h1 {{
                    margin: 0;
                    color: #ffffff;
                    font-size: 22px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }}
                .content {{
                    padding: 24px;
                    line-height: 1.6;
                    color: #1a1a1a;
                }}
                .content h2 {{
                    color: #1e40af;
                    margin: 0 0 12px 0;
                    font-size: 18px;
                }}
                .content p {{
                    margin: 0 0 12px 0;
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 16px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 12px;
                    color: #6b7280;
                    text-align: center;
                }}
                .button {{
                    display: inline-block;
                    background-color: #2563eb;
                    color: #ffffff !important;
                    padding: 12px 24px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: bold;
                    margin: 16px 0;
                }}
                .priority-critical {{ color: #dc2626; font-weight: bold; }}
                .priority-high {{ color: #ea580c; font-weight: bold; }}
                .priority-medium {{ color: #d97706; font-weight: bold; }}
                .priority-low {{ color: #059669; font-weight: bold; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 16px 0;
                    font-size: 13px;
                }}
                th {{
                    text-align: left;
                    padding: 10px;
                    background-color: #f3f4f6;
                    border-bottom: 2px solid #d1d5db;
                    font-weight: bold;
                    color: #374151;
                }}
                td {{
                    text-align: left;
                    padding: 10px;
                    border-bottom: 1px solid #e5e7eb;
                    color: #1a1a1a;
                }}
                tr:last-child td {{ border-bottom: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>NEXUS // Task Intelligence</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    Sent automatically by NEXUS AI Platform &copy; {datetime.now().year}<br/>
                    Powered by CrewAI & FastAPI // Hackathon 2025
                </div>
            </div>
        </body>
        </html>
        """

    def send_email(self, to_email, subject, html_content):
        """Low-level Gmail SMTP sender."""
        if not self.enabled:
            print(f"[EMAIL SKIP] SMTP disabled (no credentials). To: {to_email}, Subject: {subject}")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"NEXUS AI <{self.sender_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_content, "html"))

        context = ssl.create_default_context()
        try:
            print(f"[EMAIL] Attempting to send to {to_email}...")
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            print(f"[EMAIL] ✅ Sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"[EMAIL] ❌ Failed to send to {to_email}: {e}")
            return False

    def send_task_assignment(self, recipient_email, recipient_name, 
                              task_title, task_description, priority, 
                              due_date, assigned_by, meeting_title):
        subject = f"[NEXUS] New Task Assigned: {task_title}"
        content = f"""
            <h2 style="margin-top: 0;">New Task Assigned</h2>
            <p>Hi <strong>{recipient_name}</strong>,</p>
            <p>You have been automatically assigned a new task from the meeting <strong>"{meeting_title}"</strong> by our AI intelligence layer.</p>
            
            <table>
                <tr><th>Task</th><td>{task_title}</td></tr>
                <tr><th>Priority</th><td class="priority-{priority.lower()}">{priority.upper()}</td></tr>
                <tr><th>Due Date</th><td>{due_date}</td></tr>
                <tr><th>Description</th><td>{task_description}</td></tr>
                <tr><th>Assigned By</th><td>{assigned_by}</td></tr>
            </table>

            <center>
                <a href="http://localhost:5173/tasks" class="button">View Task in NEXUS</a>
            </center>
        """
        return self.send_email(recipient_email, subject, self._get_base_html(content))

    def send_escalation_alert(self, recipient_email, recipient_name,
                               task_title, escalation_reason, attempts_made):
        subject = f"[NEXUS] ⚠️ Task Escalation Alert: {task_title}"
        content = f"""
            <h2 style="margin-top: 0; color: #EF4444;">🚨 Urgent Escalation Alert</h2>
            <p>Attention <strong>{recipient_name}</strong>,</p>
            <p>NEXUS has identified a stalled task that required manager-level escalation after <strong>{attempts_made}</strong> failed autonomous resolution attempts.</p>
            
            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #EF4444; padding: 16px; margin: 20px 0;">
                <strong style="display: block; margin-bottom: 4px; color: #EF4444;">Task Stalled:</strong>
                {task_title}
            </div>

            <p><strong>Escalation Logic:</strong> {escalation_reason}</p>

            <center>
                <a href="http://localhost:5173/audit" class="button" style="background-color: #EF4444;">Review Audit Trail</a>
            </center>
        """
        return self.send_email(recipient_email, subject, self._get_base_html(content))

    def send_workflow_summary(self, recipient_email, meeting_title,
                               total_tasks, your_tasks, autonomy_score):
        subject = f"[NEXUS] Meeting Processed: {meeting_title}"
        content = f"""
            <h2 style="margin-top: 0;">Post-Meeting Intelligence Summary</h2>
            <p>NEXUS has finished processing the <strong>"{meeting_title}"</strong> transcript. Here are the key metrics from the autonomous agent workflow:</p>
            
            <div style="display: flex; justify-content: space-between; gap: 10px; margin: 20px 0;">
                <div style="flex: 1; padding: 12px; background: #080C14; border: 1px solid #1E293B; border-radius: 8px; text-align: center;">
                    <div style="color: #94A3B8; font-size: 10px; margin-bottom: 4px;">TOTAL TASKS</div>
                    <div style="font-size: 20px; font-weight: bold; color: #F1F5F9;">{total_tasks}</div>
                </div>
                <div style="flex: 1; padding: 12px; background: #080C14; border: 1px solid #1E293B; border-radius: 8px; text-align: center;">
                    <div style="color: #94A3B8; font-size: 10px; margin-bottom: 4px;">YOUR TASKS</div>
                    <div style="font-size: 20px; font-weight: bold; color: #00D4FF;">{your_tasks}</div>
                </div>
                <div style="flex: 1; padding: 12px; background: #080C14; border: 1px solid #1E293B; border-radius: 8px; text-align: center;">
                    <div style="color: #94A3B8; font-size: 10px; margin-bottom: 4px;">AUTONOMY</div>
                    <div style="font-size: 20px; font-weight: bold; color: #10B981;">{autonomy_score}%</div>
                </div>
            </div>

            <p>All tasks have been logged in the system with their corresponding owners and deadlines.</p>

            <center>
                <a href="http://localhost:5173/" class="button">Open Dashboard</a>
            </center>
        """
        return self.send_email(recipient_email, subject, self._get_base_html(content))

# Singleton instance
email_service = EmailService()

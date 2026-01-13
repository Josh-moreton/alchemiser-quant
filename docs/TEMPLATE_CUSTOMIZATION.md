# Email Template Customization Guide

This guide explains how to customize email templates in The Alchemiser notification system.

## Overview

The Alchemiser uses code-based templates (not SES stored templates) for full flexibility and version control. All templates are in:

```
layers/shared/the_alchemiser/shared/notifications/templates.py
```

## Template Structure

Each notification type has **two templates**:
1. **HTML** - Rich formatting, colors, branded header/footer
2. **Plain Text** - Fallback for text-only email clients

Both templates receive the same `context` dictionary with data.

## Available Templates

### Current Templates

1. **Daily Run SUCCESS** (`render_daily_run_success_html` / `render_daily_run_success_text`)
2. **Daily Run FAILURE** (`render_daily_run_failure_html` / `render_daily_run_failure_text`)
3. **Daily Run RECOVERED** (simple template in `_send_recovery_email`)

### Planned Templates

4. **Data Lake Update SUCCESS**
5. **Data Lake Update FAILURE**
6. **Data Lake Update RECOVERED**

## Template Components

### Shared Branding

#### HTML Header
```python
def render_html_header(component: str, status: str) -> str:
    # Returns:
    # - Gradient purple header with ⚗️ logo
    # - Component name (e.g., "Your Daily Rebalance Summary")
    # - Status bar (color-coded: green/yellow/red/blue)
```

**Customization**:
- Change colors by editing `status_colors` dict
- Update logo emoji or replace with `<img>` tag
- Adjust gradient colors

#### HTML Footer
```python
def render_html_footer() -> str:
    # Returns standard footer with system name
```

**Customization**:
- Add links (documentation, dashboard, support)
- Add legal disclaimers or compliance text
- Add company logo

#### Plain Text Header/Footer
Similar functions exist for plain text emails.

### Subject Line Format

**Strict Format** (do not change without updating epic requirements):
- **SUCCESS**: `Your Daily Rebalance Summary`
- **Other statuses**: `Your Daily Rebalance Summary — {STATUS}`

Example: `Your Daily Rebalance Summary` (success) or `Your Daily Rebalance Summary — FAILURE`

**Function**:
```python
format_subject(
    component="Your Daily Rebalance Summary",
    status="SUCCESS",  # Status only included if not SUCCESS
    env="prod",
    run_id="8f3c1a12",
    run_date=datetime.now()
)
```

## Creating a New Template

### Step 1: Define Template Functions

```python
def render_my_notification_html(context: dict[str, Any]) -> str:
    """Render HTML for My Notification.
    
    Args:
        context: Template context with data
        
    Returns:
        Complete HTML email body
    """
    header = render_html_header("My Component", context["status"])
    footer = render_html_footer()
    
    # Extract context values
    env = context.get("env", "unknown")
    run_id = context.get("run_id", "unknown")[:6]
    
    # Build body
    body = f"""
    <div style="background-color: white; padding: 30px;">
        <h2>My Custom Notification</h2>
        <p><strong>Environment:</strong> {env}</p>
        <p><strong>Run ID:</strong> {run_id}</p>
        <!-- Add your sections here -->
    </div>
    """
    
    return header + body + footer


def render_my_notification_text(context: dict[str, Any]) -> str:
    """Render plain text for My Notification."""
    header = render_text_header("My Component", context["status"])
    footer = render_text_footer()
    
    body = f"""
Environment: {context.get("env", "unknown")}
Run ID: {context.get("run_id", "unknown")[:6]}

<!-- Add your content here -->
"""
    
    return header + body + footer
```

### Step 2: Update NotificationService

In `functions/notifications/service.py`, add a new handler method:

```python
def _handle_my_notification(self, event: MyNotificationRequested) -> None:
    """Handle my custom notification event."""
    self._log_event_context(event, "Processing my notification")
    
    # Build context
    context = {
        "status": "SUCCESS",
        "env": self.stage,
        "run_id": event.correlation_id,
        # Add more fields as needed
    }
    
    # Render templates
    html_body = render_my_notification_html(context)
    text_body = render_my_notification_text(context)
    
    # Build subject
    subject = format_subject(
        component="My Component",
        status="SUCCESS",
        env=self.stage,
        run_id=event.correlation_id[:6],
    )
    
    # Send via SES
    result = send_email(
        to_addresses=self._get_recipients(),
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )
    
    if result.get("status") == "sent":
        self._log_event_context(
            event,
            f"Notification sent (message_id={result.get('message_id')})",
        )
```

### Step 3: Register Event Handler

In `NotificationService.handle_event()`:

```python
if isinstance(event, MyNotificationRequested):
    self._handle_my_notification(event)
```

## Template Best Practices

### HTML Templates

1. **Inline CSS Only**: Email clients don't support `<style>` tags or external CSS
   ```html
   <!-- ✅ Good -->
   <div style="color: #333; padding: 20px;">Content</div>
   
   <!-- ❌ Bad -->
   <div class="content">Content</div>
   <style>.content { padding: 20px; }</style>
   ```

2. **Use Tables for Layout**: Email clients have poor support for flexbox/grid
   ```html
   <table style="width: 100%;">
     <tr>
       <td style="padding: 10px;">Column 1</td>
       <td style="padding: 10px;">Column 2</td>
     </tr>
   </table>
   ```

3. **Color Coding**: Use consistent colors for status
   - **SUCCESS**: `#28a745` (green)
   - **WARNING**: `#ffc107` (yellow)
   - **FAILURE**: `#dc3545` (red)
   - **RECOVERED**: `#17a2b8` (blue)

4. **Font Stacks**: Use safe font stacks
   ```css
   font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
   ```

5. **Max Width**: Keep email width ≤ 800px for readability
   ```html
   <body style="max-width: 800px; margin: 0 auto;">
   ```

6. **Test Across Clients**: Different email clients render HTML differently
   - Gmail (web, mobile)
   - Outlook (Windows, macOS, web)
   - Apple Mail
   - Consider using [Email on Acid](https://www.emailonacid.com/) for testing

### Plain Text Templates

1. **Keep it Simple**: Plain text is fallback - don't try to mimic HTML layout
2. **Use ASCII Art Sparingly**: Borders and separators are fine
   ```
   =====================================
   SECTION TITLE
   =====================================
   ```
3. **Indentation**: Use consistent indentation for hierarchy
4. **Line Length**: Keep lines ≤ 80 characters for readability

### Context Design

1. **Type Safety**: Document expected fields in docstring
2. **Defaults**: Always provide defaults for optional fields
   ```python
   env = context.get("env", "unknown")
   ```
3. **Validation**: Validate critical fields before rendering
4. **No Sensitive Data**: Never include credentials, API keys, or PII

## Styling Guide

### Current Brand Colors

- **Primary Purple**: `#667eea` (light) → `#764ba2` (dark) for gradients
- **Success Green**: `#28a745`
- **Warning Yellow**: `#ffc107`
- **Error Red**: `#dc3545`
- **Info Blue**: `#17a2b8`
- **Neutral Gray**: `#6c757d`
- **Background**: `#f8f9fa` for sections
- **Border**: `#e9ecef` for separators

### Typography

- **Headers**: `28px` (h1), `20px` (h2), `16px` (h3)
- **Body**: `16px`
- **Small**: `14px` (footer, captions)
- **Code/Monospace**: `12px`, use `<pre>` tags

### Spacing

- **Section Padding**: `20px`
- **Element Margin**: `10px` between related items, `20px` between sections
- **Border Radius**: `6px` for sections, `4px` for small elements

## Testing Templates

### Manual Testing

1. **Create test context** in Python shell:
   ```python
   from the_alchemiser.shared.notifications.templates import *
   
   context = {
       "status": "SUCCESS",
       "env": "dev",
       "run_id": "test123",
       # Add all required fields
   }
   
   html = render_daily_run_success_html(context)
   text = render_daily_run_success_text(context)
   
   # Save to files for inspection
   with open("/tmp/test_email.html", "w") as f:
       f.write(html)
   ```

2. **View in browser**: Open `/tmp/test_email.html` in your browser

3. **Test send** via SES:
   ```python
   from the_alchemiser.shared.notifications.ses_publisher import send_email
   
   send_email(
       to_addresses=["your-email@example.com"],
       subject="Test Email",
       html_body=html,
       text_body=text,
   )
   ```

### Automated Testing

Add snapshot tests in `tests/notifications/test_templates.py`:

```python
def test_daily_run_success_template_snapshot():
    """Snapshot test for Daily Run SUCCESS template."""
    context = {
        "status": "SUCCESS",
        "env": "prod",
        "run_id": "abc123",
        # ... complete context
    }
    
    html = render_daily_run_success_html(context)
    
    # Assert key elements are present
    assert "⚗️ The Alchemiser" in html
    assert "SUCCESS" in html
    assert "abc123" in html
    assert "Daily Run" in html
```

## Common Customizations

### 1. Add Company Logo

Replace emoji with image in `render_html_header()`:

```python
<img src="https://your-cdn.com/logo.png" alt="Logo" 
     style="max-width: 200px; height: auto;">
```

### 2. Change Color Scheme

Update `status_colors` dict in `render_html_header()`:

```python
status_colors = {
    "SUCCESS": "#00c851",  # Your custom green
    "FAILURE": "#ff4444",  # Your custom red
    # ...
}
```

### 3. Add Footer Links

In `render_html_footer()`:

```html
<p style="margin: 10px 0;">
  <a href="https://dashboard.example.com">Dashboard</a> |
  <a href="https://docs.example.com">Documentation</a> |
  <a href="mailto:support@example.com">Support</a>
</p>
```

### 4. Add Disclaimer

In `render_html_footer()`:

```html
<p style="font-size: 12px; color: #999; margin-top: 20px;">
  This is an automated notification from your trading system.
  Do not reply to this email. For support, contact team@example.com.
</p>
```

### 5. Conditional Sections

Use Python conditionals in template:

```python
if context.get("warnings"):
    body += """
    <div style="background-color: #fff3cd; padding: 20px;">
        <h3>⚠️ Warnings</h3>
        <ul>
    """
    for warning in context["warnings"]:
        body += f"<li>{warning}</li>\n"
    body += """
        </ul>
    </div>
    """
```

## Troubleshooting

### HTML Not Rendering

- **Issue**: Email shows HTML code instead of rendering
- **Solution**: Ensure you're passing `html_body` and `text_body` correctly to SES

### Styles Not Applied

- **Issue**: Colors/fonts not showing
- **Solution**: Use inline styles only. No external CSS or `<style>` tags.

### Template Too Long

- **Issue**: Email is truncated or not delivered
- **Solution**: Keep HTML < 100KB. Truncate long stack traces or logs.

### Missing Data

- **Issue**: Template shows "unknown" or "N/A" for fields
- **Solution**: Ensure context includes all required fields before rendering

## References

- [Email HTML Best Practices](https://www.campaignmonitor.com/css/)
- [Responsive Email Design](https://www.smashingmagazine.com/2017/01/introduction-building-sending-html-email-for-web-developers/)
- [Can I Email?](https://www.caniemail.com/) - CSS support across email clients

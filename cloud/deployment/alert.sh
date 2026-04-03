#!/bin/bash
# Alert Script for Digital FTE Health Monitoring
#
# Sends alerts via SMS (Twilio), Push (Pushover/ntfy.sh), and Email
# Called by Monit when health checks fail
#
# Usage: alert.sh [service_name] [event_type] [message]
# Based on spec.md FR-032 and User Story 5.

set -e

# Configuration (load from environment or config file)
CONFIG_FILE="${ALERT_CONFIG_FILE:-/opt/digital-fte/.alert-config}"

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Alert channels (set to "true" to enable)
ENABLE_SMS="${ENABLE_SMS:-false}"
ENABLE_PUSH="${ENABLE_PUSH:-false}"
ENABLE_EMAIL="${ENABLE_EMAIL:-false}"

# Twilio configuration (for SMS)
TWILIO_ACCOUNT_SID="${TWILIO_ACCOUNT_SID:-}"
TWILIO_AUTH_TOKEN="${TWILIO_AUTH_TOKEN:-}"
TWILIO_FROM_NUMBER="${TWILIO_FROM_NUMBER:-}"
TWILIO_TO_NUMBER="${TWILIO_TO_NUMBER:-}"

# Pushover configuration (for push notifications)
PUSHOVER_APP_TOKEN="${PUSHOVER_APP_TOKEN:-}"
PUSHOVER_USER_KEY="${PUSHOVER_USER_KEY:-}"

# ntfy.sh configuration (alternative push provider)
NTFY_TOPIC="${NTFY_TOPIC:-}"
NTFY_SERVER="${NTFY_SERVER:-https://ntfy.sh}"

# Email configuration
EMAIL_TO="${EMAIL_TO:-}"
EMAIL_FROM="${EMAIL_FROM:-alerts@digital-fte.local}"
SMTP_HOST="${SMTP_HOST:-localhost}"

# Parse arguments
SERVICE_NAME="${1:-unknown}"
EVENT_TYPE="${2:-alert}"
MESSAGE="${3:-Health check failed}"

# Build alert message
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
HOSTNAME=$(hostname)

ALERT_TITLE="[ALERT] Digital FTE: $SERVICE_NAME"
ALERT_BODY="Service: $SERVICE_NAME
Event: $EVENT_TYPE
Time: $TIMESTAMP
Host: $HOSTNAME
Message: $MESSAGE"

echo "Sending alert for $SERVICE_NAME ($EVENT_TYPE)"

# Function: Send SMS via Twilio
send_sms() {
    if [ "$ENABLE_SMS" != "true" ]; then
        echo "SMS alerts disabled"
        return 0
    fi

    if [ -z "$TWILIO_ACCOUNT_SID" ] || [ -z "$TWILIO_AUTH_TOKEN" ]; then
        echo "Error: Twilio credentials not configured"
        return 1
    fi

    echo "Sending SMS alert..."

    # Truncate message for SMS (160 char limit)
    SMS_MESSAGE="[Digital FTE] $SERVICE_NAME: $EVENT_TYPE - $MESSAGE"
    SMS_MESSAGE="${SMS_MESSAGE:0:160}"

    curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json" \
        --data-urlencode "From=$TWILIO_FROM_NUMBER" \
        --data-urlencode "To=$TWILIO_TO_NUMBER" \
        --data-urlencode "Body=$SMS_MESSAGE" \
        -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
        -s -o /dev/null -w "HTTP %{http_code}\n"

    if [ $? -eq 0 ]; then
        echo "✓ SMS alert sent"
    else
        echo "✗ SMS alert failed"
    fi
}

# Function: Send push notification via Pushover
send_pushover() {
    if [ "$ENABLE_PUSH" != "true" ]; then
        echo "Push alerts disabled"
        return 0
    fi

    if [ -z "$PUSHOVER_APP_TOKEN" ] || [ -z "$PUSHOVER_USER_KEY" ]; then
        echo "Pushover not configured, skipping"
        return 0
    fi

    echo "Sending Pushover notification..."

    curl -s -X POST https://api.pushover.net/1/messages.json \
        -d "token=$PUSHOVER_APP_TOKEN" \
        -d "user=$PUSHOVER_USER_KEY" \
        -d "title=$ALERT_TITLE" \
        -d "message=$ALERT_BODY" \
        -d "priority=1" \
        -o /dev/null -w "HTTP %{http_code}\n"

    if [ $? -eq 0 ]; then
        echo "✓ Pushover notification sent"
    else
        echo "✗ Pushover notification failed"
    fi
}

# Function: Send push notification via ntfy.sh
send_ntfy() {
    if [ "$ENABLE_PUSH" != "true" ]; then
        echo "Push alerts disabled"
        return 0
    fi

    if [ -z "$NTFY_TOPIC" ]; then
        echo "ntfy.sh not configured, skipping"
        return 0
    fi

    echo "Sending ntfy.sh notification..."

    curl -s -X POST "$NTFY_SERVER/$NTFY_TOPIC" \
        -H "Title: $ALERT_TITLE" \
        -H "Priority: high" \
        -H "Tags: warning" \
        -d "$ALERT_BODY" \
        -o /dev/null -w "HTTP %{http_code}\n"

    if [ $? -eq 0 ]; then
        echo "✓ ntfy.sh notification sent"
    else
        echo "✗ ntfy.sh notification failed"
    fi
}

# Function: Send email alert
send_email() {
    if [ "$ENABLE_EMAIL" != "true" ]; then
        echo "Email alerts disabled"
        return 0
    fi

    if [ -z "$EMAIL_TO" ]; then
        echo "Error: Email recipient not configured"
        return 1
    fi

    echo "Sending email alert..."

    # Use mail command if available
    if command -v mail &> /dev/null; then
        echo "$ALERT_BODY" | mail -s "$ALERT_TITLE" "$EMAIL_TO"
        if [ $? -eq 0 ]; then
            echo "✓ Email alert sent"
        else
            echo "✗ Email alert failed"
        fi
    else
        echo "Warning: 'mail' command not found, skipping email"
    fi
}

# Send alerts via all enabled channels
send_sms
send_pushover
send_ntfy
send_email

# Log to syslog
logger -t digital-fte-alert "$ALERT_TITLE: $MESSAGE"

echo "Alert processing complete"
exit 0

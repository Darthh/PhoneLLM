# Run once, in an ELEVATED PowerShell. Private (home wifi) networks only.
New-NetFirewallRule -DisplayName "PhoneLLM" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -Profile Private

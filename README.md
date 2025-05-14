# EE Electricity Price Notification

This project automatically fetches electricity price data from Nord Pool and posts the data to a specified Telegram channel every day at 8 AM UTC. It uses the **Telegram Bot API** for sending messages and **GitHub Actions** for scheduling the daily task.

## Features

- Fetches electricity price data for Estonia from the Nord Pool API.
- Sends daily price updates to a specified Telegram channel.
- Runs automatically every day at 8 AM UTC using GitHub Actions.

## Requirements

- **Telegram Bot Token**: You'll need to create a bot via [BotFather](https://core.telegram.org/bots#botfather) on Telegram and get a token.
- **Telegram Channel ID**: You'll need the channel ID where the bot will post the updates. This can be a private or public channel.
- **.env file**: Store your Telegram bot token and channel ID in a `.env` file.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/ee_electricity_price_notification.git
   cd ee_electricity_price_notification
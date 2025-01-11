# AI Financial News Agent

A Python-based AI agent that automatically collects, analyzes, and stores financial news using Google's Gemini AI and Brave Search API. The project also includes a Bitcoin price tracking component.

## Features

- **Financial News Collection**: Automatically searches and collects news from reputable financial sources (Bloomberg, Reuters, CNBC, FT)
- **AI-Powered Analysis**: Uses Google's Gemini AI to generate concise summaries of financial articles
- **Bitcoin Price Tracking**: Monitors and stores Bitcoin price data
- **Data Storage**: Stores all collected data in Supabase for easy access and analysis
- **Robust Error Handling**: Comprehensive logging and error management system

## Technologies Used

- Python 3.9+
- Google Gemini AI API
- Brave Search API
- Supabase
- BeautifulSoup4
- Requests
- Logging

## Database Schema (Supabase)

### Tables

1. **finance_news**
   - `id`: bigint (Primary Key, Auto-increment)
   - `created_at`: timestamp with timezone
   - `title`: text
   - `url`: text
   - `finance_info`: text
   - `source`: text

2. **btc_price**
   - `id`: bigint (Primary Key, Auto-increment)
   - `created_at`: timestamp with timezone (Default: now())
   - `price`: float

## Setup

1. Clone the repository
2. Install dependencies:

```
## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
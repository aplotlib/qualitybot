# qualitybot
# Quality Bot

A Streamlit-powered AI chatbot for quality-related questions and assistance.

## Overview

Quality Bot is an AI assistant built with Streamlit and OpenAI's GPT models. It provides an intuitive interface for asking questions about quality assurance, quality management, and related topics.

## Features

- Clean, modern chat interface
- Customizable AI model settings
- Conversation history management
- Downloadable chat transcripts
- Responsive design

## File Structure

The repository contains three main files:

- `main.py`: The Streamlit application code
- `key.py`: API key configuration
- `requirements.txt`: Required dependencies

## Setup Instructions

### Local Development

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/qualitybot.git
   cd qualitybot
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run main.py
   ```

### Streamlit Cloud Deployment

1. Fork or push this repository to your GitHub account
2. Sign in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and select this repository
4. Set the main file path to `main.py`
5. Deploy!

## Security Note

For production deployment, it's recommended to use Streamlit's secrets management instead of storing the API key directly in the code. See [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management) for details.

## License

[Include your license information here]

## Contact

[Your contact information]

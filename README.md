# UK Biobank Search Assistant

An AI assistant that helps you search and understand UK Biobank data. Just ask questions in plain English (or Chinese) and get helpful answers about the data fields you need.

## What it does

- Ask questions like "show me heart disease fields" and get relevant results
- Explains what each data field means in simple terms  
- Helps you find related fields you might have missed
- Works in both English and Chinese
- Has a simple web interface you can use

## How it works

The AI assistant can:
- Look up specific field details when you give it a field ID
- Search for fields using keywords 
- Show you what's available in different categories (like "cardiovascular" or "mental health")
- Explain what those confusing encoding values actually mean
- Suggest other fields that might be useful for your research
- Website: https://ukbb.cabbages.cyou
## Getting started

You'll need:
- Python 3.8 or newer
- The UK Biobank database file (ukb_datadict.db)
- An API key from Zhipu AI

### Setup

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API key:
   ```
   GLM_API_KEY=your_api_key_here
   ```

3. Run the app:
   ```bash
   python main.py
   ```

4. Open your browser to `http://localhost:8000`

## Example questions you can ask

**Finding fields:**
- "What heart disease fields are available?"
- "Show me depression-related measurements"
- "Are there any diabetes fields?"

**Getting details:**
- "What does field 31 mean?"
- "Explain field 22001"

**Exploring categories:**
- "What's in the mental health category?"
- "Show me all cardiovascular fields"

**Getting recommendations:**
- "What fields are good for studying obesity?"
- "Recommend fields for cancer research"


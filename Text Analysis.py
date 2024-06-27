import pandas as pd
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import re


# Function to read words from a text file
def read_words_from_file(file_path):
    with open(file_path, 'r') as file:
        words = file.read().splitlines()
    return set(words)

# Function to read stop words from multiple files
def read_stop_words(stop_word_files):
    stop_words = set()
    for file_path in stop_word_files:
        stop_words.update(read_words_from_file(file_path))
    return stop_words

# Function to calculate syllable count per word
def syllable_count(word):
    vowels = "aeiouy"
    word = word.lower()
    count = 0
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count += 1
    return count

def clean_text(text):
    # Remove newline characters (\n)
    cleaned_text = text.replace('\n', ' ').replace('\xa0',' ')

    # Remove special characters and non-breaking space (\xa0)
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)

    return cleaned_text

def extract_title_and_content(url):
    try:
        # Fetch the HTML content of the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        html_content = response.text

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract the title (h1)
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else ''

        # Extract the content (div.td-post-content)
        content_div = soup.find('div', class_='td-post-content')
        content = content_div.text.strip() if content_div else ''

        # Concatenate title and content into a single string
        text = f'{title} {content}'

        # Clean the text
        cleaned_text = clean_text(text)

        return cleaned_text

    except (requests.RequestException, ValueError, AttributeError):
        # Handle exceptions (e.g., connection error, bad response, attribute error)
        return None

# Function to calculate text analysis parameters
def calculate_parameters(cleaned_text, positive_words, negative_words, stop_words):
    cleaned_words = [word.lower() for word in word_tokenize(cleaned_text) if word.isalnum() and word.lower() not in stop_words]

    

    positive_score = sum(1 for word in cleaned_words if word in positive_words)
    negative_score = sum(1 for word in cleaned_words if word in negative_words)
    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (len(cleaned_words) + 0.000001)

    sentence_list = sent_tokenize(cleaned_text)
    average_sentence_length = len(cleaned_words) / len(sentence_list)

    complex_word_count = sum(1 for word in cleaned_words if syllable_count(word) > 2)
    percentage_complex_words = (complex_word_count / len(cleaned_words)) * 100

    fog_index = 0.4 * (average_sentence_length + percentage_complex_words)

    avg_words_per_sentence = len(cleaned_words) / len(sentence_list)
    complex_word_count = sum(1 for word in cleaned_words if syllable_count(word) > 2)
    word_count = len(cleaned_words)
    syllable_per_word = sum(syllable_count(word) for word in cleaned_words) / word_count

    personal_pronouns = len(re.findall(r'\b(?:I|we|my|ours|us)\b', cleaned_text, flags=re.IGNORECASE))

    avg_word_length = sum(len(word) for word in cleaned_words) / word_count

    return [
            positive_score, negative_score, polarity_score, subjectivity_score,
            average_sentence_length, percentage_complex_words, fog_index,
            avg_words_per_sentence, complex_word_count, word_count,
            syllable_per_word, personal_pronouns, avg_word_length
        ]


# Load words from text files
positive_words = read_words_from_file('positive-words.txt')
negative_words = read_words_from_file('negative-words.txt')
stop_word_files = ['StopWords_Auditor.txt','StopWords_Currencies.txt','StopWords_Generic.txt', 'StopWords_DatesandNumbers.txt','StopWords_GenericLong.txt','StopWords_Geographic.txt','StopWords_Names.txt']  # Add your stop word files here
stop_words = read_stop_words(stop_word_files)

# Load data from Input.xlsx
 # Replace with the path to your 'Input.xlsx' file
df_input = pd.read_excel('Input.xlsx' )

# Create columns for the calculated parameters
parameter_columns = [
    'POSITIVE SCORE', 'NEGATIVE SCORE', 'POLARITY SCORE', 'SUBJECTIVITY SCORE',
    'AVERAGE SENTENCE LENGTH', 'PERCENTAGE OF COMPLEX WORDS', 'FOG INDEX',
    'AVERAGE NUMBER OF WORDS PER SENTENCE', 'COMPLEX WORD COUNT', 'WORD COUNT',
    'SYLLABLE PER WORD', 'PERSONAL PRONOUNS', 'AVERAGE WORD LENGTH'
]

# Calculate parameters for each URL and add them to the DataFrame
for index, row in df_input.iterrows():
    url = row['URL']  # Assuming 'URL' is the column containing the URL
    data = extract_title_and_content(url)
    

    if data is not None:
        parameters = calculate_parameters(data, positive_words, negative_words, stop_words)
        df_input.loc[index, parameter_columns] = parameters
    else:
        # Drop rows with missing data
        df_input.drop(index, inplace=True)

# Save the updated DataFrame to 'Output Data Structure.xlsx'

df_input.to_excel('Output Data Structure.xlsx', index=False)

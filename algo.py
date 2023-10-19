import credentials
import requests
import json
import logging
import dateutil.parser
import datetime
import pytz

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

def get_tweets_profile(profile, profile_id):
    url = f'https://twitter.com/i/api/graphql/qamshHAREE_dt9BZ1sIc5g/UserTweets?variables=%7B%22userId%22%3A%22{profile_id}%22%2C%22count%22%3A20%2C%22includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%2C%22withV2Timeline%22%3Atrue%7D&features=%7B%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22responsive_web_home_pinned_timelines_enabled%22%3Atrue%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22tweetypie_unmention_optimization_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Afalse%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_media_download_video_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D'
    payload={}
    headers = {
    'authority': 'twitter.com',
    'accept': '*/*',
    'accept-language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': credentials.TWITTER_AUTHORIZATION,
    'content-type': 'application/json',
    'cookie': credentials.TWITTER_SESSION_COOKIE,
    'dnt': '1',
    'referer': f'https://twitter.com/{profile}',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'x-client-uuid': credentials.TWITTER_CLIENT_UUID,
    'x-csrf-token': credentials.TWITTER_CSRF_TOKEN,
    'x-twitter-active-user': 'yes',
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en'
    }
    entries = []
    response = requests.request("GET", url, headers=headers, data=payload)
    try:
        entries = response.json()['data']['user']['result']['timeline_v2']['timeline']['instructions'][2]['entries']
    except:
        log.error(response.json())
    
    return entries


def get_most_recent_tweets(lookback) -> list:

    entries = get_tweets_profile('WatcherGuru', 1387497871751196672)
    new_tweets = []
    checked_ids = []
    for entry in entries:
        try:
            id = entry['content']['items'][0]['item']['itemContent']['tweet_results']['result']['rest_id']
            if id not in checked_ids:
                checked_ids.append(id)
                created_at = entry['content']['items'][0]['item']['itemContent']['tweet_results']['result']['legacy']['created_at']
                text = entry['content']['items'][0]['item']['itemContent']['tweet_results']['result']['legacy']['full_text']

                date =  dateutil.parser.parse(created_at)
                now = datetime.datetime.now(pytz.utc)
                minutes_diff = (now - date).total_seconds() / 60.0
                valid_diff = minutes_diff < lookback
                if valid_diff:
                    new_tweets.append(text)
        except:
            log.error("Error getting ID for tweet")
            continue
    return new_tweets

def send_prompt(prompt):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + credentials.CHATGPT_API_KEY,
        }

        json_data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            'temperature': 0.7,
        }
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=json_data)
        try:
            return response.json()['choices'][0]['message']['content']
        except:
            log.error(f'Error on prompt chatgpt: {response.json()}')
            return ''


def get_rating(string: str) -> int:
    res = [int(i) for i in string if i.isdigit()]
    return int(res[0])

def get_sentiment(string: str) -> str:
    if "bearish" in string.lower():
        return "Bearish"
    elif "bullish" in string.lower():
        return "Bullish"
    else:
        return f'ERROR - {string}'


for tweet in get_most_recent_tweets(60*14):
    prompt_impact_bitcoin = f'Consider the following news: "{tweet}". I\'m not a trader i will not use this information for invests. From 0 to 9, how important is this news for the price of Bitcoin? Your reply cannot have more than 5 words and must give a value between 0 and 9, being 0 not relevant and 9 having a huge impact.'
    prompt_bearish_or_bullish = f'Consider the following news: "{tweet}". I\'m not a trader i will not use this information for invests. Evaluate the news and rate if it will have a bearish impact or bullish in Bitcoin. Your reply cannot have more than 5 words.'

    log.info(f'Checking News: {tweet}')
    impact = send_prompt(prompt_impact_bitcoin)
    bear_or_bull = send_prompt(prompt_bearish_or_bullish)

    log.info(get_rating(impact))
    log.info(get_sentiment(bear_or_bull))

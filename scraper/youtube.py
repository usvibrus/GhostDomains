import logging
import requests

from scraper.config import Config

logger = logging.getLogger(__name__)


def search_channels(query='', max_results=50, page_token=None):
    """
    Search YouTube for channels created before 2022.
    Returns list of channel IDs and next page token.
    Cost: 100 quota units per call.
    """
    if not Config.has_youtube():
        logger.warning("YouTube API key not configured. Skipping YouTube pipeline.")
        return [], None

    params = {
        'part': 'snippet',
        'type': 'channel',
        'maxResults': min(max_results, 50),
        'publishedBefore': Config.YOUTUBE_CHANNELS_BEFORE,
        'key': Config.YOUTUBE_API_KEY,
        'order': 'relevance',
    }
    if query:
        params['q'] = query
    if page_token:
        params['pageToken'] = page_token

    try:
        resp = requests.get(
            'https://www.googleapis.com/youtube/v3/search',
            params=params,
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            channel_ids = [
                item['snippet']['channelId']
                for item in data.get('items', [])
                if 'channelId' in item.get('snippet', {})
            ]
            next_token = data.get('nextPageToken')
            logger.info(f"YouTube search returned {len(channel_ids)} channels")
            return channel_ids, next_token
        elif resp.status_code == 403:
            logger.error("YouTube API quota exceeded!")
            return [], None
        else:
            logger.error(f"YouTube search failed: {resp.status_code} - {resp.text[:200]}")
            return [], None
    except Exception as e:
        logger.error(f"YouTube search error: {e}")
        return [], None


def fetch_channel_details(channel_ids):
    """
    Fetch channel details (description, subscriber count, creation date).
    Batches up to 50 IDs per call.
    Cost: 1 quota unit per call (cheap!).
    Returns list of channel data dicts.
    """
    if not Config.has_youtube() or not channel_ids:
        return []

    results = []

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i + 50]

        try:
            resp = requests.get(
                'https://www.googleapis.com/youtube/v3/channels',
                params={
                    'part': 'snippet,statistics',
                    'id': ','.join(batch),
                    'key': Config.YOUTUBE_API_KEY,
                },
                timeout=15,
            )

            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('items', []):
                    snippet = item.get('snippet', {})
                    stats = item.get('statistics', {})
                    results.append({
                        'channel_id': item['id'],
                        'name': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'created_date': snippet.get('publishedAt', '')[:10],
                        'subscriber_count': int(stats.get('subscriberCount', 0)),
                    })
            elif resp.status_code == 403:
                logger.error("YouTube API quota exceeded during channel fetch!")
                break
            else:
                logger.warning(f"Channel fetch failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Channel fetch error: {e}")

    logger.info(f"Fetched details for {len(results)} channels")
    return results


# Pre-defined search queries — targeting channels likely to have personal websites
# Focus on professionals, creators and businesses (not pure gaming/entertainment)
SEARCH_QUERIES = [
    # Professionals / freelancers
    'web design portfolio',
    'graphic design freelancer',
    'photographer portfolio',
    'digital marketing agency',
    'SEO consultant blog',
    'web developer tutorial',
    'UX design tips',
    'video editor freelance',
    # Niche bloggers / content creators
    'personal finance blog',
    'food recipe blog',
    'travel blog vlog',
    'fitness coaching',
    'health wellness coach',
    'online business tips',
    'real estate investing',
    'photography tips tutorial',
    # Small business / education
    'small business marketing',
    'online course creator',
    'podcast creator tips',
    'music producer beats',
    'art tutorial painting',
    'coding bootcamp tutorial',
    'DIY home improvement',
    'interior design tips',
]

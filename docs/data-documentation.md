
# Web Scraped Content Datasets for YOU-DARE Far-Right Gender Controversy Mapping

[toc]

## 1. Introduction

This report provides documentation for the data collection "Web Scraped Content Datasets for YOU-DARE Far-Right Gender Controversy Mapping", collected as part of the [Horizon Europe YOU-DARE project](https://cordis.europa.eu/project/id/101178147). The purpose of this document is to describe data contents as well as how data was collected, what types of data were produced, and which tools and techniques were used. The report is intended as methodological documentation rather than a code-level manual. Therefore, the focus is on general approaches, assumptions, and design decisions rather than implementation details.

All data collection and curation was done by [CALDISS at Aalborg University](https://www.en.caldiss.aau.dk/).

The goal of the data collection pipeline was to gather raw data in a structured format that could later be reviewed, processed, and used for analysis in the project.

Data was collected from a researcher-curated selection of actors - influencers, groups, political parties, organization - from three platforms: Websites, YouTube and Telegram. 

All software used for data collection and post-processing is available via CALDISS GitHub. 

- Repository containing software for data collection: https://github.com/CALDISS-AAU/YOU-DARE_scrapers
- Repository containing post-processing software (sub-directory of project repository): https://github.com/CALDISS-AAU/RP_YOU-DARE/tree/master/raw-data

## 2. Data Contents and Structure

The collected datasets contain news articles, forum threads, videos, and Telegram posts gathered from online platforms across eight European countries: Denmark (DK), France (FR), Italy (IT), Hungary (HU), Romania (RO), Spain (ES), Sweden (SE), and the United Kingdom (UK). A full overview of all sources, their associated platforms, and included fields for each country is provided in Appendix A. Data collection was carried out for each country independently, and the resulting data is stored in the JSON Lines format (.jsonl), where each line constitutes a single self-contained observation — either an article, a thread, or a post depending on the data source.

For each country, the output is written to a combined JSON Lines file named according to the pattern:
`{country}_YOUDARE-WEBDATA_combined.jsonl`

- Each line represents one observation (article, video, or thread)
- Fields are consistent within each dataset type.
- Missing values are represented as null regardless of field otherwise containing single or multiple values.

Each entry/row is assigned a unique entry_ID, constructed from the country abbreviation, an abbreviated actor code, a platform code, and a running row number. The `entry_ID` is placed as the first field in the output.

As fields vary depending on platform, field description are provided per platform collected from (websites, Flashback Forum, YouTube, Telegram).

### 2.1 Common data fields

The following data fields are used across all entries regardless of platform.

| Field            | Description                                                                 | Type   |
|------------------|-----------------------------------------------------------------------------|--------|
| entry_ID         | Unique id for each entry in the combined dataset for each country          | string |
| source           | Unique identifier for the source extracted from the url                    | string |
| actor            | The name of the actor or organisation behind the website                   | string |
| platform         | Platform type where the content was published (YouTube, Telegram or Website)| string |
| scrape_date      | Date for the day of collection in ISO 8601 date format (YYYY-MM-DD)                                         | string |
| publication_date | Date of publication for specific entry in source-specific date formating   | string |

### 2.2 Website-specific fields

The following fields are specific to data collected from websites.
Each website represents a single article. 

| Field                | Description                                                                  | Type                          |
| -------------------- | ---------------------------------------------------------------------------- | ----------------------------- |
| article_link         | URL of the individual article                                                | string                        |
| article_title        | The main title of the article                                                | string                        |
| author               | The author of the article                                     | string                        |
| article_categories   | Categories, tags, or topics associated with the article                      | array of strings               |
| article_text         | The main textual content of the article, including subtitles and inline text | string                        |
| image_links          | URLs to images embedded in the article                                       | array of strings               |
| embedded_media_links | Links to embedded media (e.g. YouTube, social media)                         | array of strings               |
| links_in_text        | Hyperlinks found within the article text (e.g. references)                   | array of strings               |
| other_items          | Any additional gathered for a specific source. Content varies by source and uses non-standardized source-specific keys                   | object           |

### 2.3 Flashback Forum-specific fields

The following fields are specific to data collected from the online forum "Flashback". Due to the forum structure, Flashback data differs from standard website data. Each entry represents a thread rather than a single article.

| Field                                       | Description                                                                                                                     | Type   |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------ |
| post_link                                          | URL of the thread                                                                                                               | string      |
| post_title                                         | Title of the thread                                                                                                             | string      |
| publication_date                                   | Date of the original post                                                                                                       | string |
| post_author                                        | Author of the original post                                                                                                     | string      |
| post_categories                                    | Forum categories associated with the thread                                                                                     | array of strings      |
| replies | Array of objects for each reply (each object with the keys: label (post/comment), author, date, tag (unique tag for each comment used for referencing) and text) | array of objects |
| thread_text                                        | Combined text of the original post and all comments | string      |
| links_in_text | Aggregated links across all comments in the thread                                                                    | array of strings      |

### 2.4 YouTube-specific fields

The following fields are specific to data colleced from YouTube. Each entry represents a video. A video is included regardless of whether any speech was identified and transcribed.

| Field            | Description                     | Type   |
| ---------------- | ------------------------------- | ------ |
| video_title      | Title of the video              | string |
| source           | Channel name or handle          | string |
| publication_date | Date the video was published    | string |
| video_link       | URL to the video                | string |
| video_id         | Unique YouTube video identifier | string |
| video_text | Auto-transcribed text of speech in the video based on downloaded .m4a file of the video's audio track (see section 6 for further detail) | string | 


### 2.5 Telegram-specific fields

The following fields are specific to data collected from Telegram.
Telegram data is collected via Telepathy. Replies and posts are merged so that one entry represents one thread (original post followed by replies).

**Thread-level fields:**
| Field    | Description                                                                     | Type   |
| --------------- | ------------------------------------------------------------------------------- | ------ |
| message_ID         | Unique identifier for the Telegram post assigned by Telegram's API                                         | integer       |
| thread_text | Combined post and replies into a single structured text. Replies separated by newlines using three dashes (---) as separator. | string |
| timestamp       | Timestamp of when the first post of the thread was made. ISO 8601 datetime string (with timezone offset) | string |
| message_text       | Content of the first post of the thread                                                             | string |
| URL | URL to the specific post | string |
| user_ID | Unique numeric identifier for the user authoring the post | integer |
| replies | All replies and associated metadata included in the thread | array of objects | 

**Reply-level fields:**
If a post contains replies, the original reply texts along with metadata are contained in the replies field. Each object in the field contains the fields specificed below.

| Field    | Description                                                                     | Type   |
| --------------- | ------------------------------------------------------------------------------- | ------ |
| message_ID         | Unique identifier for the Telegram post assigned by Telegram's API                                         | integer       |
| message_text       | Content of the reply post                                                             | string |
| URL | URL to the specific post | string |
| timestamp       | Timestamp of when the reply was made. ISO 8601 datetime string (with timezone offset) | string |
| user_ID | Unique numeric identifier for the user authoring the post | integer |
| reply_to_ID | message_ID that the post is a reply to (corresponds to a message_ID in a thread-level entry) | integer |
| is_reply | Binary indicator whether post is a direct reply to the original post. 1 if yes, 0 otherwise | integer | 
| is_reply_via_post | Binary indicator whether post is a reply via tagging the original post. 1 if yes, 0 otherwise | integer | 



## 3. Overview of Data Collection Methods

Data collection in the YOU-DARE project relied on four main methodological approaches:

- Collection of YouTube videos using [*pytubefix*](https://pypi.org/project/pytubefix/9.5.1/) (and in some cases [yt-dlp](https://github.com/yt-dlp/yt-dlp))
- Collection of Telegram data using [*Telepathy*](https://github.com/prose-intelligence-ltd/Telepathy-Community)
- Scraping of static websites using [*Scrapy*](https://docs.scrapy.org/en/2.13/)
- Scraping of dynamic websites using [*Playwright*](https://pypi.org/project/playwright/1.55.0/) in combination with *Scrapy*

These approaches were necessary because the targeted sources differed significantly in their technical structure. Some websites expose content directly through HTML, while others require interaction such as scrolling or clicking. Similarly, platforms such as YouTube and Telegram require platform-specific tools due to authentication, APIs, and media handling.

### 3.1 General Assumptions Across Scrapers

Although different tools were used, the data collection methods shared several general assumptions:

First, it was assumed that relevant content could be accessed either through HTML structure or through controlled interaction with a webpage or platform. For websites, this meant that content could be identified through CSS or XPath selectors. For platforms such as YouTube and Telegram, it was assumed that metadata and content could be retrieved via available libraries or APIs.

Second, it was assumed that content structure would be sufficiently stable to allow rule-based extraction. However, in practice, several sources deviated from this assumption and required custom handling.

Third, it was assumed that repeated runs of scrapers could be used to incrementally collect data. This was particularly important for large or unstable sources.

#### 3.1.1 Exceptions with regard to data collection
Although the data collection pipeline in the YOU-DARE project was designed to follow consistent methodological principles, several platform-specific and technical constraints resulted in deviations from the ideal data structure. These exceptions are important to document, as they affect data completeness, comparability, and interpretation. For an in-depth view of each collected field for each source by country, please consult Appendeix A.


### 3.2 Websites
Website scraping relied on extracting structured information from HTML content. However, due to prevalent variation in website design and structure, not all fields could be consistently collected across sources.

In some cases, relevant metadata such as publication dates, authors, or categories were either not present in the HTML or were embedded in non-standard formats that could not be reliably parsed. As a result, certain fields may be missing or only partially populated for specific sources.

A subset of websites was accessed through archived versions (e.g. via the Wayback Machine) rather than through their live versions. These sources were treated as standard website scrapers in terms of methodology, meaning that the same scraping logic and extraction procedures were applied. The only difference lies in the access point, where archived snapshots were used instead of live pages.

However, the use of archived pages may introduce additional variability. Archived content can be incomplete, inconsistently captured, or missing dynamic elements, which may affect both data availability and metadata quality.


### 3.3 YouTube
YouTube data collection was constrained by limitations of the YouTube API and third-party tools. In particular, not all metadata fields were consistently accessible for all videos.

For some videos, publication dates could not be retrieved due to API restrictions. Furthermore, rate limiting imposed by YouTube affected the completeness of data collection, especially for channels with a large number of videos. In such cases, the scraper may not have captured the full set of available videos within a single run.

These limitations mean that some YouTube entries may have missing or incomplete metadata, particularly with regard to publication dates.

### 3.4 Telegram
Telegram data collection was affected by constraints in the Telegram API and the structure of message data.

One key limitation is that replies containing images or other media are not always fully captured by the scraping process. This can result in “false negatives,” where a reply exists but is not recorded in the dataset, leading to incomplete thread reconstruction.

In addition, not all Telegram channels support replies. For channels without reply functionality, the dataset consists only of standalone posts, which limits the ability to analyse interaction patterns or conversational structures.

Finally, variations in how replies are stored and accessed required post-processing steps to reconstruct threads, which may introduce minor inconsistencies in how reply relationships are represented.

## 4. Static Website Scraping (Scrapy)
### 4.1 Method
Static website scraping was used for sources where content could be accessed through direct HTTP requests. In this context, a “static” site refers to a site where relevant content is present in the HTML response and does not require user interaction to be revealed.

Scrapy was used as the main framework for these scrapers. Each scraper followed a general workflow where a front page was loaded, article links were extracted, and each article page was visited to collect detailed information.

The general workflow consisted of loading one or more start URLs, extracting links to articles, following those links, and parsing the article content. If pagination was available, the scraper followed “next page” links until all pages had been processed or a predefined limit had been reached.

To improve efficiency and reproducibility, previously scraped links were stored and compared against newly discovered links. This ensured that articles were not collected multiple times across runs.

### 4.2 Deviations from Standard Pattern
Several scrapers deviated from the standard static pattern.

Some websites contained all relevant information directly on the front page. In these cases, no separate article parsing step was required.

Other websites did not support pagination, meaning that the scraper only needed to process a single page.

Some sources were accessed through the Wayback Machine due to limited accessibility of the original site.

There were also cases where the scraper explicitly ignored robots.txt restrictions, which represents a deviation from standard ethical scraping practices, however, it is within the boundaries of what is allowed for scientific research.

## 5. Dynamic Website Scraping (Playwright + Scrapy)
### 5.1 Method
Dynamic website scraping was used for sources where content is not fully available in the initial HTML response. Instead, content is loaded dynamically through JavaScript and requires interaction such as scrolling or clicking.

To handle this, Playwright was used to simulate a browser environment. Two main interaction patterns were observed. In some cases, content was loaded progressively as the user scrolled down the page. In other cases, content was loaded by clicking a “load more” button. Some websites used a combination of both mechanisms. The scraper first opened the webpage using Playwright and performed the necessary interactions to reveal all relevant content. Once the content had been rendered, Scrapy was used to extract and store the data similarly to static scrapers.

## 6. YouTube Data Collection (pytubefix)
### 6.1 Method
YouTube data was primarily collected using the pytubefix library. This tool was used to extract metadata from videos and download audio tracks.

For channels with a large volume of content or stricter access restrictions, yt-dlp was used as a complementary tool when the size of the source was too large for PyTube to handle.

Each scraper accessed either a channel URL or a YouTube playlist, iterated through available videos, extracted metadata such as title and publication date, and downloaded audio files. The metadata was stored in JSON Lines format, while audio files were saved separately.

In some cases, authentication was required in order to access age-restricted content, and this introduced additional complexity.

In order to create  video_text an automatic transcriber based on the whisper model was utilized on each collected video. Thus, this field is the said content of each video in text format.

## 7. Telegram Data Collection (Telepathy)
### 7.1 Method
Telegram data was collected using the Telepathy tool, which provides access to Telegram channels through the platform’s API.

The program authenticated using a Telegram account and then collected posts and, where available, replies from specified channels. The data was exported in structured formats for further processing in the form of .csv files.

### 7.2 Special Considerations
Telegram data collection required authentication and therefore depended on access credentials.

## 8. Post-processing
### 8.1 Overview of the Post-processing Pipeline
Post-processing was performed in order to combine data collected across scrapers to a single combined JSON Lines file for each country.

The main goal of the post-processing was to ensure that data from websites, YouTube, Telegram, and Flashback could be handled consistently while still preserving platform-specific differences where relevant. It also reduced redundant storage, simplified tracking of processed files, and made it easier to identify missing, failed, or potentially overlooked datasets.

### 8.2 Input Discovery and Platform Detection
The post-processing pipeline iterates over each scraped source from each country and performed platform-specific post-processing based on the platform data was colelcted from: Website, Flashback, YouTube or Telegram.

This distinction is important because the different platforms store data in different formats and require different reading and standardisation logic. Telegram data, for example, may consist of separate post and reply files in CSV format, while website and YouTube data are typically read from JSON Lines files.

### 8.3 Platform-specific Processing Pipelines
Once a dataset has been classified by platform, it is passed through a platform-specific processing pipeline.

#### 8.3.1 Website Standardisation
Website datasets were standardised to a fixed article-level schema. This standardisation ensured both consistent variable names and consistent value formats across sources, even when the original scraper outputs differed slightly in structure.

The website standardiser performs several operations. First, it ensures that all expected keys are present in the correct order. Missing fields are added with `None` values. Second, it cleans and restructures certain fields that may appear under different names or in inconsistent forms across datasets.

For example, subtitle fields are merged into the beginning of `article_text` when relevant, and reference lists are packed into `other_items`. Legacy or source-specific keys such as `external_links`, `youtube_links`, `categories`, and `themes_text` are mapped into the standard fields `links_in_text`, `embedded_media_links`, and `article_categories`.

The standardiser also normalises values that incorrectly represent missingness. Strings such as `"none"`, `"null"`, or `"nothing else"` are converted to actual null values where appropriate. Fields that should always behave as lists, such as `image_links`, `article_categories`, `embedded_media_links`, and `links_in_text`, are coerced into list format. Empty lists or dictionaries are later converted back to null at top level in the final output.

This procedure makes the website datasets structurally consistent and reduces the amount of source-specific irregularity in the final combined files.

It should be noted that in the case of websites, standardisation was essential due to inconsistency in how website scrapers were developed throughout the project. However, the website scrapers have since been standardized, meaning that if one were to recollect all scraped data using the uploaded scrapers on Github (https://github.com/CALDISS-AAU/YOU-DARE_scrapers), this standardization step would not be required.

#### 8.3.2 Flashback Standardisation
Flashback data required a separate standardisation procedure because it represents forum threads rather than ordinary articles. 

The standardization involves extracting individual thread components such as label, author, date, tag, and text from the original block structure and turns them into a `replies` list of structured dictionaries. At the same time, it rebuilds `thread_text` into a cleaner concatenated plain-text representation.

The Flashback standardiser also renames and restructures certain fields. For example, `categories` is renamed to `post_categories`, and `external_links` is mapped to `links_in_text`. It additionally removes fields that are considered consistently empty or irrelevant in the standardised format, such as `embedded_media_links`, `image_links`, `other_items`, and `post_HTML`.

A further source-specific feature is date normalisation. The standardiser handles Swedish relative date expressions such as `Idag` (“today”) and `Igår` (“yesterday”) by converting them into explicit dates based on the scrape date. This ensures consistent date formatting of the `publication_date` field for all Flashback entries. 

#### 8.3.3 YouTube Standardisation
YouTube datasets were standardised through a comparatively lightweight procedure, because their schema was already more constrained than the website data. The standardiser first checks that all expected columns are present. These include:

- `scrape_date`
- `video_title`
- `source`
- `publication_date`
- `video_link`
- `video_id`
- `video_text`

If any required key is missing, the standardisation step raises an error. This makes it easier to identify incomplete or malformed YouTube datasets during processing.

The main transformation applied to YouTube data concerns the publication date. Some YouTube datasets (those collected through yt-dlp) store dates in compact numeric form such as `20250608`. These values are normalised into an ISO-like format such as `2025-06-08`. Dates that are already stored in ISO format are preserved, while missing values remain null.

Compared with the website and Telegram pipelines, the YouTube standardisation is therefore primarily a schema validation and date-normalisation step.

#### 8.3.4 Telegram Standardisation
Telegram post-processing mainly involves joining data from the collected posts and replies, if present, as these were retrieved as separate datasets. The purpose of the Telegram standardiser is to reconstruct these into thread-like units where each top-level post becomes a single combined observation.

The standardisation function first derives the source name either from the file path or from the post data itself. It then harmonises column names across post and reply datasets and fills missing values with empty strings during intermediate processing. The data is sorted by message ID in order to preserve chronological and structural order.

For each top-level Telegram post, the function creates a thread-level record containing metadata such as message ID, timestamp, URL, user ID, and source. It then gathers associated replies in two ways. First, it adds replies found in the reply archive. Second, it recursively identifies replies that are themselves represented as posts pointing back to the original post through `reply_to_ID`. This recursive step allows the pipeline to include nested reply structures rather than only direct replies.

The final output contains both a `thread_text` field and a structured `replies` field. The `thread_text` field concatenates the post text and all associated reply texts into a single thread-level text representation separated by delimiters. The `replies` field preserves the individual reply records and distinguishes between replies found directly in the reply archive and replies represented as posts. In this way, the Telegram pipeline produces a more analysis-ready representation of conversational structure, by excluding irrelevant metadata and combining related data into post threads.

### 8.4 Adding Actor, Platform, and Entry Identifiers
After platform-specific standardisation, the post-processing pipeline adds additional metadata to distinguish between actors and platforms collected from.

The `actor` variable is added using a country-specific source-to-actor mapping file. This step ensures that source names can be mapped onto a standardised actor label for easy isolation of data from specific actors.

The `platform` variable is added to indicate whether the observation originated from Website, Flashback, YouTube, or Telegram data. This makes it possible to isolate data from specific platforms.

### 8.5 Output of the Post-processing Stage
The output of the post-processing stage is a country-level combined raw dataset in JSON Lines format. Each line represents one standardised observation, but the internal structure of the observation still reflects the platform from which it originated. In other words, the pipeline standardises data enough to make it combinable and traceable, while still preserving platform-relevant distinctions.

This means that the combined dataset does not flatten all platform differences away. Instead, it creates a unified storage format with explicit metadata about actor and platform, consistent naming conventions, and platform-appropriate standardisation of fields.

The result is a set of combined raw data files that can serve as the basis for later annotation, analysis, or additional transformation.


## Appendix A: Overview of collected fields by country
Below, tables are provided for each country listing all sources, their associated platform, the URLs collected from and the included data fields.

### DK

| Source                          | Actor          | Platform  | Start URLs | Included fields |
|---------------------------------|----------------|-----------|-----------------|-----------------|
| Maniphesto Core                 | Maniphesto     | Website   | https://maniphesto.com/blog/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items, article_HTML |
| Retten til Liv                  | Retten til liv | Website   | https://rettentilliv.dk/category/nyhed/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items, article_HTML |
| Modstrømmen                     | Modstrømmen    | Website   | https://modstroemmen.dk/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_text, image_links, article_HTML |
| Manderådet                      | Manderådet     | Website   | https://manderaadet.dk/nyt-fra-manderadet/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_text, links_in_text, article_HTML|
| Nordfront                       | NordFront      | Website   | https://www.nordfront.dk/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links, embedded_media_links, links_in_text, article_HTML|
| Stop Islamiseringen af Danmark  | Stop Islamiseringen af Danmark (SIAD) | Website   | https://siaddk.wordpress.com/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links, links_in_text, article_HTML|
| Danmarks Demokraternes Ungdom   | Danmarks-Demokraterne Ungdom | Website   | https://ddungdom.dk/antiwoke/<br/>https://ddungdom.dk/social-og-familie/<br/>https://ddungdom.dk/maerkesager/<br/>https://ddungdom.dk/nyheder/<br/>https://ddungdom.dk/wp-content/uploads/2025/04/DDU-Principprogram-PDF.pdf | entry_ID, actor, platform, scrape_date, source, article_link, article_title, article_text, image_links, external_links |
| Dansk Folkepartis Ungdom        | Dansk Folkepartis Ungdom (DFU) | Website   | https://www.dfungdom.dk/ | entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, article_text, image_links |
| Generation Identitær            | Generation Identitær | Website  | https://identitaer.dk/category/presse | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links, links_in_text, article_HTML|
| Reel Ligestilling               | Reel Ligestilling | Website   | https://reelligestilling.dk/category/indhold/ligestillingsnyt/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_text, image_links, links_in_text, article_HTML|
| DF Ungdom YouTube               | Dansk Folkepartis Ungdom (DFU) | YouTube   | https://www.youtube.com/@danskfolkepartisungdom351/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Manderådet YouTube              | Manderådet | YouTube   | https://www.youtube.com/@manderaadet/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Maniphesto YouTube              | Maniphesto | YouTube   | https://www.youtube.com/@ManiphestoMen/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Maniphesto Core Telegram        | Maniphesto | Telegram  | https://t.me/maniphestocore | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
| Rasmus Munch | Rasmus Munch Søndergaard | YouTube | https://www.youtube.com/user/Ralledang/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
| Dansk regnbueraad - Nyheder  | Dansk Regnbueråd | Website | https://www.danskregnbueraad.dk/nyt |entry_ID, actor, platform, scrape_date, publication_date, source, author, article_link, article_title, article_text, article_HTML, image_links, embedded_media_links, link_in_text|
| Dansk regnbueraad - Artikler | Dansk Regnbueråd | Website| https://www.danskregnbueraad.dk/artikler | entry_ID, actor, platform, scrape_date, source, article_link, article_title, article_text, image_links, article_HTML|
| Dansk regnbueråd | Dansk Regnbueråd | YouTube | https://www.youtube.com/@danskregnbuerad-danishrain4275/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Retten til liv | Retten til Liv | YouTube | https://www.youtube.com/@rettentilliv5654/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |

### FR

| Source | Actor | Platform | Start URLs | Included fields |
| -------- |-----| -------- | -------- | -------- |
| Alex Hitchens     | Alex Hitchens | YouTube     | https://www.youtube.com/@thefrenchitch/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
| Charlotte Dornellas| Charlotte d'Ornellas | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text| https://www.youtube.com/@ChdOrnellas/videos ||
|Isuel and Anne| Iseul & Anne - Le Café des Antigones | YouTube| https://www.youtube.com/@IseuletAnne/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
|Jordan Bardella| Jordan Bardella |YouTube|https://www.youtube.com/@J_Bardella| entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
| Julien Rochedy| Julien Rochedy | YouTube| https://www.youtube.com/@Julien.Rochedy/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
|Le Rator| Le Raptor Dissident | YouTube| https://www.youtube.com/@LeRaptor/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
|Le Syndicat de la Familie| Le Syndicat de la Famille |YouTube|https://www.youtube.com/@LeSyndicatdelaFamille/videos| entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
|Marion Marechal| Marion Marechal | YouTube| https://www.youtube.com/@MarionMarechalOfficiel/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
|Nemesis Media| Collectif Némésis |YouTube|https://www.youtube.com/@CollectifNemesis_Media| entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
|Thais d'Escufon| Thaïs d'Escufon | YouTube| https://www.youtube.com/@ThaisdEscufonYT/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text|
|Generation Zemmour| Generation Z |Website|https://www.generation-zemmour.fr/articles|scrape_date, source, article_link, article_title, publication_date, author, article_text, links_in_text|
| Le Cocarde etudiante | La Cocarde Étudiante | Website| https://cocardeetudiante.com/articles/',<br/>https://cocardeetudiante.com/articles/page/2/<br/>https://cocardeetudiante.com/articles/page/3/<br/>https://cocardeetudiante.com/articles/page/4/<br/>https://cocardeetudiante.com/articles/page/5/<br/>https://cocardeetudiante.com/communiques/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items|
| Les Identitaires| Les Identitaires |Website|https://les-identitaires.fr/articles/|entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text|
|Papacito| Papacito |Telegram|https://t.me/papacitofdp| entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|RNJ Officiel| RNJ |Telegram|https://t.me/RNJofficiel| entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|


### IT


| Source | Actor | Platform | Start URLs | Included Fields |
| -------- | ---- | -------- | -------- | -------- |
| Blocco Studentsco    | Blocco Studentesco | Website     | https://www.bloccostudentesco.org/?s=genere<br/>https://www.bloccostudentesco.org/?s=femminismo<br/>https://www.bloccostudentesco.org/?s=LGBT<br/>https://www.bloccostudentesco.org/?s=aborto<br/>https://www.bloccostudentesco.org/?s=virilita | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_text, image_links|
|Casa Pound Italia|Casa Pound| Website| https://casapounditalia.org/category/cpi-news/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_text, image_links|
|Family Day|Family Day| Website| https://familyday.info/#notizie | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items|
|Gioventu Nazionale|Gioventu' nazionale| Website| https://www.gioventunazionale.it/news/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items|
|Il Rami Spogli| I Rami Spogli| Website| https://www.ramispogli.it/<br />https://www.ramispogli.it/page/2/<br />https://www.ramispogli.it/page/3/ |entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items|
| Pro Vita e Famiglia|Pro Vita e Famiglia| Website| https://www.provitaefamiglia.it/petizione | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items|
|Il Redpillatore|Il Redpillatore| Website| https://www.ilredpillatore.org/category/societa'<br/>https://www.ilredpillatore.org/category/societa/antifemminismo | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items|
|Uominie Donne|Uomini e Donne in Movimento| Website| https://www.uominibeta.org/category/articoli/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_categories, article_text, image_links, embedded_media_links, links_in_text, other_items|
|Dici Raggi|Comunita' militante dei dodici raggi, Do.ra.| Telegram| https://t.me/dodiciraggi | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Essere Uomo|Essere Uomo| YouTube| https://www.youtube.com/@EssereUomo/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Lealta Azione|Lealta' Azione|YouTube|https://www.youtube.com/@lealtaazione6032/videos| entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Yasmin Pani|Yasmina Pani| YouTube| https://www.youtube.com/@YasminaPani/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Rete Dei Patrioti|La Rete dei Patrioti| Telegram| https://t.me/retedeipatrioti | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
| Isabella Tovaglieri (Lega, yout wing) | Isabella Tovaglieri (Lega, yout wing)|YouTube|https://www.youtube.com/@isatovaglieri/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|La Fionda |La Fionda|Telegram |https://t.me/la_fionda | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|


### HU
| Source | Actor | Platform |  | Included Fields |
| -------- | ---- | -------- | -------- | -------- |
|Betyarsereg|Betyársereg| Website| https://betyarsereg.hu | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links, links_in_text|
|Fidez Hirek| Fidesz|Website|https://fidesz.hu/hirek| entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links, links_in_text|
|Hvim.hu|HVIM|Website|https://www.hvim.hu/|entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links, links_in_text|
|Legio Hungaria|Legio Hungaria (LH)| Website| https://legiohungaria.org/ | entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links|
|Viktor Órban  Beszedek| Viktor Orbán|Website|https://miniszterelnok.hu/beszedek/|entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text|
|Viktor Orban Hirek| Viktor Orbán|Website|https://miniszterelnok.hu/hirek/|entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text|
|Viktor Orban Interjuk| Viktor Orbán|Website|https://miniszterelnok.hu/interjuk| entry_ID, actor, platform, scrape_date, source, article_link, article_title, article_text, publication_date|
|Duro Dora|Dóra Dúró|Telegram|https://t.me/durodora| entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Fidelitas| Fidelitas|YouTube|https://www.youtube.com/@fidelitashu/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Fidesz videos|Fidesz| YouTube| https://fidesz.hu | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|⚔️ Incze Béla|Béla Incze| Telegram| https://t.me/InczeBelaLegionarius | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Jobbszélső 🇭🇺|Jobbszélső| Telegram| https://t.me/jobbszelso | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Légió Hungária|Legio Hungaria (LH)| Telegram| https://t.me/legiohungaria | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Mi Magunk (Hvim.hu) |HVIM| YouTube| https://www.youtube.com/@mimagunk/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Mi Hazánk Ifjai|Mi Hazánk Ifjai| Telegram| https://t.me/mihazankifjai | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Möm| MÖM|YouTube|https://www.youtube.com/@magyaronvedelmimozgalom/videoss|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Novák Előd|Előd Novák| Telegram| https://t.me/novakelod | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|NovakElodHivatalos|Előd Novák| YouTube| https://www.youtube.com/@NovakElodHivatalos/videos |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|ProjectLegionary|Project Legionary| YouTube| https://www.youtube.com/@ProjectLegionary/videos |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Totoczkai László| László Toroczkai|YouTube|https://www.youtube.com/c/ToroczkaiL%C3%A1szl%C3%B3Hivatalos/videos| entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|🛑 Toroczkai László|László Toroczkai| Telegram| https://t.me/toroczkai | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|1orbanviktor| Viktor Orbán|YouTube|https://www.youtube.com/@1orbanviktor/videos| entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Budaházy György |György Budaházy |YouTube|https://www.youtube.com/@budahazygyorgy2659/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Budaházy Edda |Edda Budaházy |YouTube|https://www.youtube.com/@hozzvilagramegegymagyartmo8703/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Dóra Dúró YouTube |Dóra Dúró |YouTube|https://www.youtube.com/@DuroDoraHivatalos/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |


### RO
| Source |Actor | Platform | Start URLs | Included Fields |
| -------- |----| -------- | -------- | -------- |
|Claudiu.Tarziu| Claudiu Târziu| YouTube| https://www.youtube.com/@Claudiu.Tarziu<br/>https://www.youtube.com/playlist?list=PLSfRvqOFLFUHnsVwtWTl3k0HEudFqgTkc<br/>https://www.youtube.com/playlist?list=PLSfRvqOFLFUEBdX9Q0Eor34eYuv7SKdo9<br/>https://www.youtube.com/playlist?list=PLSfRvqOFLFUH8spjKSSPJNq1CurHrbcdt<br/>https://www.youtube.com/watch?v=mo8Pc-VsNZQ |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Comunitatea Identitară România| Comunitatea Identitară |YouTube|https://www.youtube.com/@comunitateaidentitara8517/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Comunitatea Identitară România| Comunitatea Identitară | Telegram| https://t.me/comunitatea_identitara | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Comunitatea Identitară România| Comunitatea Identitară | Website| https://comunitateaidentitara.com/category/blog<br/>https://comunitateaidentitara.com/category/actiuni<br/>https://comunitateaidentitara.com/category/podcast |entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links|
| Cultura Vietii |Cultura Vieții |Website|https://www.culturavietii.ro/| entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_text, image_links, links_in_text|
|Noua Dreapta| Noua Dreaptă | Website| https://www.nouadreapta.org/actiuni.html <br/>https://www.nouadreapta.org/acasa.html<br />https://www.nouadreapta.org/opinii.html |entry_ID, actor, platform, scrape_date, source, article_link, article_title, article_text, image_links, embedded_media_links|
|Pro Vita| ProVita | Website| https://asociatiaprovita.ro/blog<br/>https://asociatiaprovita.ro/activitati/scrisori<br/>https://asociatiaprovita.ro/activitati/analize-comentarii<br/>https://asociatiaprovita.ro/activitati/relatii-internationale |entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, article_text, image_links|
|Rost| Rost| Website| https://www.rostonline.ro/category/politic<br/>https://www.rostonline.ro/category/religios<br/>https://www.rostonline.ro/category/uniunea-europeana<br/>https://www.rostonline.ro/category/cultural |entry_ID, actor, platform, scrape_date, source, article_link, article_title, publication_date, author, article_text, image_links, links_in_text|
|George Simion |George Simion |YouTube|https://www.youtube.com/@georgesimionoficial/videos<br/>https://www.youtube.com/playlist?list=PL8rhFWFhcwYWl986aTHgUGAewg6ag-D_-<br/>https://www.youtube.com/playlist?list=PL8rhFWFhcwYV2JWvJqV0F2oRmXPqPzX8s|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Noua Dreapta| Noua Dreaptă | YouTube| https://www.youtube.com/@NouaDreaptaTV/videos |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Noua Dreaptă Oficial|Noua Dreaptă | Telegram| https://t.me/nouadreapta | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|🇹🇩 Fani Revista Rost| Rost |Telegram|https://t.me/revistaRost| entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Mihail Neamțu | Mihail Neamțu |YouTube|https://www.youtube.com/@mihailneamtuneoficial<br/>https://www.youtube.com/playlist?list=PLi0C8irncgr9JkutgKTPhL-VnRZhLCfnm<br/>https://www.youtube.com/playlist?list=PLi0C8irncgr-ERnKcECO-L6DpYElM-tXp|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Activenews | Activenews |Website |https://www.activenews.ro/stiri<br/>https://www.activenews.ro/opinii<br/>https://www.activenews.ro/externe<br/>https://www.activenews.ro/ucraina<br/>https://www.activenews.ro/razboi-in-orient<br/>https://www.activenews.ro/alegeri-2024<br/>https://www.activenews.ro/cultura<br/>https://www.activenews.ro/covid<br/>https://www.activenews.ro/covid-era-covid-si-marea-resetare-the-great-reset<br/>https://www.activenews.ro/economie |entry_ID, actor, platform, scrape_date, source, article_link, article_title, article_title, article_categories, article_text, image_links, links_in_text, embedded_media_links|
|Cezar Ionașcu | Cezar Ionașcu |YouTube |https://www.youtube.com/@cezarionascu71/videos<br/>https://www.youtube.com/@cezarionascu71/streams<br/>https://www.youtube.com/playlist?list=PLnB67EAd_txZ81eBrY4EKMpyMHPG7h2wr<br/>https://www.youtube.com/playlist?list=PLhwbvb1FMcC2BoZdNGTyUP7_3y8Xr1otU<br/>https://www.youtube.com/watch?v=U61WrjhnJSU<br/>https://www.youtube.com/watch?v=gIBXN1gFBVI<br/>https://www.youtube.com/watch?v=ZuSgAlfk9s8<br/>https://www.youtube.com/watch?v=zy9IwbdtJ84<br/>https://www.youtube.com/watch?v=D6RDsGSVP1A<br/>https://www.youtube.com/watch?v=uUOb1WuyPBI<br/>https://www.youtube.com/watch?v=U-hPIhGzWc4<br/>https://www.youtube.com/watch?v=pyPuc63m8x0<br/>https://www.youtube.com/watch?v=XUIsW7EMoKo<br/>https://www.youtube.com/watch?v=_yX9ElPMM3g<br/>https://www.youtube.com/watch?v=OZa4FuOcIaM<br/>https://www.youtube.com/watch?v=dtqA_LpUJtY |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Vlad Caraiman | Vlad Caraiman |YouTube |https://www.youtube.com/@alphaacademyro<br/>https://www.youtube.com/@alphaacademyro/videos<br/>https://www.youtube.com/watch?v=FTIGYGavSjk<br/>https://www.youtube.com/watch?v=PnJXQfPjZIE<br/>https://www.youtube.com/watch?v=dpR0lCJk7jI<br/>https://www.youtube.com/watch?v=urz9ImJy6Ss<br/>https://www.youtube.com/watch?v=_D8eQ0n1WA4 |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Casus Belli |Casus Belli |Telegram|https://t.me/casusbelli2021| entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Naționaliștii Autonomi Timișoara | Naționaliștii Autonomi Timișoara |Telegram |https://t.me/nat88org | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Liga Studenților Iași | Liga Studenților Iași |Telegram |https://t.me/ligastudentilor | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|


### ES
| Source | Actor | Platform | Start URLs | Included Fields |
| -------- | ---- | -------- | -------- | -------- |
|Alt Right España Noticias| Alt-Right España| Telegram| https://t.me/AltRightEspana | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Alvise_Oficial| Alvise Pérez| YouTube| https://www.youtube.com/@Alvise_Oficial/videos |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Alvise Pérez| Alvise Pérez | Telegram| https://t.me/AlvisePerez | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Anthony Corey Sanchez | Anthony Corey Sánchez |YouTube|https://www.youtube.com/@COREYCAT/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Aliança Catalana | Aliança Catalana |Telegram|https://t.me/catalunyaac| entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|DesokupaTV| Desokupa | YouTube| https://www.youtube.com/@DesokupaTV/videos |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|estudiantspelcanvi | Estudiants pel Canvi |YouTube|https://www.youtube.com/@estudiantspelcanvi/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|HerQles| HerQles |Telegram|https://t.me/herQles|entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Info Vlogger| InfoVlogger | YouTube| https://www.youtube.com/@InfoVlogger/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|LA CATALUNYA WOKE| La Catalunya Woke |YouTube|https://www.youtube.com/@LaCatalunyaWoke/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Red Pill Podcast | RedPill Podscast |YouTube|https://www.youtube.com/@redpillpodcast_/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Revuelta| Revuelta | Telegram| https://t.me/Revuelta_es | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|robertovaquero_|Roberto Vaquero |YouTube|https://www.youtube.com/@robertovaquero_/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Roma Gallardo| Roma Gallardo | YouTube| https://www.youtube.com/@romagallardo7504/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Núcleo Nacional | Núcleo Nacional |Telegram|https://t.me/unetenucleonacional|entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies |
|Vito Quiles 🇪🇸 | Vito Quiles |Telegram|https://t.me/vitoquilestelegram| entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
|Wall Street Wolverine | WallStreet Wolverine|YouTube|https://www.youtube.com/@WallStreetWolverine/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Vox | Vox |YouTube|https://www.youtube.com/c/VoxEspa%C3%B1aTV/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |


### SE
| Source                                              | Actor | Platform  |   | Included Fields |
|-----------------------------------------------------|-------|----------|-----------------|-----------------|
| Aktivklubb_Sverige (AKS (gammal) FÖLJ NYA!)         | Aktivklubb Sverige | Telegram | http://t.me/Aktivklubb_Sverige | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
| Gym XIV (Banned on Apple)                           | Gym XIV | Telegram | http://t.me/GymXIV | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
| GYM XIV                                             | Gym XIV | Telegram | http://t.me/GymXIV2 |entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
| The Golden One                                      | The Golden One | Telegram | http://t.me/thegoldenone | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
| WB Stockholm                                        | White Boys Stockholm | Telegram | http://t.me/WBsthlm | entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
| Alternativ for Sverige                              | Alternativ för Sverige | YouTube  | https://www.youtube.com/@AfS_riks/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Christian Peterson                                 | Christian Peterson | YouTube  | https://www.youtube.com/@assarchristian/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Det Fria Sverige                                   | Det fria Sverige | YouTube  | https://www.youtube.com/@DetfriaSverige/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Inblick med Nick                                   | Nick Alinia | YouTube  | https://www.youtube.com/@NickAlinia/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Riks TV                                            | Riks TV | YouTube  | https://www.youtube.com/c/Riksstudios/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| SD_Micke                                           | SD-Micke | YouTube  | https://www.youtube.com/@SD_Micke/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| SDMonkan                                           | SD-Monkan | YouTube  | https://www.youtube.com/@SDMonkan/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| The Golden One                                     | The Golden One | YouTube  | https://www.youtube.com/@TheGoldenOne/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
| Flashback - Censur och Yttrandefrihet              | Flashback: Free speech subforum | Website  | https://www.flashback.org/f69-censur-och-yttrandefrihet-51006 | entry_ID, actor, platform, scrape_date, source, publication_date, post_link, post_title, post_author, categories, thread_text, external_links |
| Flashback - Integration och invandring             | Flashback: Integration and migration subforum | Website  | https://www.flashback.org/f226-integration-och-invandring-51007 | entry_ID, actor, platform, scrape_date, source, publication_date, post_link, post_title, post_author, categories, thread_text, external_links |
| Flashback - Nationalsocialism, fascism och nationalism | Flashback: National socialis & nationalism subforum | Website | https://www.flashback.org/f34-nationalsocialism-fascism-och-nationalism-51006 | entry_ID, actor, platform, scrape_date, source, publication_date, post_link, post_title, post_author, categories, thread_text, external_links |
| Nordiska Motståndsrörelsen                         | Nordiska motståndsrörelsen | Website  | https://xn--motstndsrrelsen-llb70a.se/ | entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_text, embedded_media_links, external_links, article_HTML |
| NordFront (SWE)                                    | Nordfront | Website  | https://nordfront.se/ | entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_text, image_links, links_in_text, article_HTML, article_categories |
| Nya Tider                                          | Nya Tider | Website  | https://www.nyatider.nu | entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_categories, article_text, image_links, links_in_text, article_HTML |
| Samnytt                                            | Samnytt | Website  | https://samnytt.se/category/ledare<br/>https://samnytt.se/category/debatt<br/>https://samnytt.se/category/kronikor | entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, article_text, image_links, links_in_text, article_categories, article_HTML |

### UK
| Source | Actor | Platform | Start URLs | Included Fields |
| -------- | ----- | -------- | -------- | -------- |
|DangerField| Dangerfield |YouTube |https://www.youtube.com/@DangerfieldChris/videos | entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Hamza Ahmed| Hamza Ahmed |YouTube|https://www.youtube.com/@Hamza97/videos|entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Reform UK| Reform UK | YouTube| https://www.youtube.com/@ReformUKOfficial/videos |entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|Zoomer Historian| Zoomer Historian |YouTube|https://www.youtube.com/@ZoomerHistorian/videos| entry_ID, actor, platform, scrape_date, video_title, source, publication_date, video_link, video_id, video_text |
|GB News| GB NEWS |Website|https://www.gbnews.com/opinion/|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, article_text, article_categories|
|Homeland Party News| The Homeland Party  |Website|https://homelandparty.org/news/category/news/|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_categories, article_text|
|Homeland Party - Our Thinking| The Homeland Party |Website|https://homelandparty.org/our-thinking/|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_categories, article_text|
|Lotus Eaters| Lotus eaters |Website|https://www.lotuseaters.com/category/entertainment<br/>https://www.lotuseaters.com/category/news<br/>https://www.lotuseaters.com/category/analysis|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_categories, article_text, image_links, embedded_media_links, external_links|
|The Mallard| The Mallard |Website|https://mallarduk.com/category/comment/<br/>https://mallarduk.com/category/culture/|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, article_text, author, categories, embedded_media_links, image_links, external_links|
|Mansworld Magazine| Mansworld Magazine |Website|https://mansworldmag.online/category/interview/<br/>https://mansworldmag.online/category/essay/|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_categories, article_text, image_links|
|Modernity| Paul Joseph Watson |Website|https://modernity.news/|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, author, article_categories, article_text, image_links|
|Reform UK - our Contract with you| Reform UK |Website|https://assets.nationbuilder.com/reformuk/pages/253/attachments/original/1718625371/Reform_UK_Our_Contract_with_You.pdf?1718625371|entry_ID, actor, platform, scrape_date, source, article_link, article_text|
|Steve Laws| Steve Laws |Website|https://stevelawsreport.co.uk/|entry_ID, actor, platform, scrape_date, publication_date, source, article_link, article_title, article_text, categories, image_links, external_links|
|Reform UK| Reform UK |Telegram|https://t.me/reformuk|entry_ID, actor, platform, message_ID, thread_text, message_text, URL, timestamp, user_ID, source, replies|
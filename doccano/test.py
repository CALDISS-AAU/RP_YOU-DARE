from .functions import Doccano_Functions, Transcriber_data_Functions 

''' To run this scraper from bash do the following:
        python -m YOU-DARE.doccano.test
'''

''' TESTING Doccano_Functions:
        # input_data_path = '/work/YOU-DARE/scrapers/data/Denmark/nordfront_SPIDER/data_nordfront_SPIDER.jl' # Nordfront - fuldt datasæt
        input_data_path = '/work/YOU-DARE/scrapers/data/Denmark/dansk_regnbueraad_artikler_SPIDER/data_dansk_regnbueraad_artikler_SPIDER.jl' # Dansk regnbueråd artikler - mangler publication_dates

        keywords_list = [
                'Hit*',
                'Antiwoke',
                'Trump',
                'Jesus',
                'Transkøn*',
                'Maskulin',
                'Patriarki',
                'Skilsmisse',
                'Privilegie',
                'Far'
        ]

        doccano = Doccano_Functions() # Instanciate the class before using it's funtions
        # df = doccano.prepare_data_for_doccano(input_data_path) # No filtering
        df = doccano.prepare_data_for_doccano(input_data_path, from_date='2025-03-01', keywords=keywords_list) # Date test

        print(df)
'''

transcriber_prep = Transcriber_data_Functions()

# input_file_path = '/work/YOU-DARE/scrapers/data/Denmark/manderaadet_YT/transcribed/16 organisationer nægter at anerkende forældrefremmedgørelse__1g4juFrCHX0_large-v3_da.json'
# text_block = transcriber_prep.extract_text_from_jsonl(input_file_path)
# print(text_block)

# transcripts_folder = '/work/YOU-DARE/scrapers/data/Denmark/manderaadet_YT/transcribed'
# output_path = f'{transcripts_folder}/combined_text_dataset_TEST.jl'
# transcriber_prep.make_text_dataset_from_transcriptions(transcripts_folder, output_path)

# dataset_path = '/work/YOU-DARE/scrapers/data/Denmark/manderaadet_YT/videos.jl'
# transcript_path = '/work/YOU-DARE/scrapers/data/Denmark/manderaadet_YT/transcribed/combined_text_dataset_TEST.jl'
# transcriber_prep.merge_datasets_on_audio_name(dataset_path, transcript_path)

dataset_path = '/work/YOU-DARE/scrapers/data/Denmark/manderaadet_YT/videos.jl'
transcriptions_dir = '/work/YOU-DARE/scrapers/data/Denmark/manderaadet_YT/transcribed'

transcriber_prep.add_transcribed_text_to_video_data(dataset_path, transcriptions_dir)
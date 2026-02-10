"""Currently unused"""
def telegram_to_threads(post_csv_path, replies_csv_path=None, sep=';'):

        ## Read data
        posts_df = pd.read_csv(post_csv_path, sep=sep, engine='python', on_bad_lines='skip')
        try:
            replies_df = pd.read_csv(replies_csv_path, sep=sep, engine='python', on_bad_lines='skip') if replies_csv_path else None
        except FileNotFoundError:
            replies_df = None
            print(f"There are no replies found for this Telegram source.")

        # Derive source from posts
        source = posts_df['To'].value_counts().index[0]
        
        # list for threads
        threads = []

        ## Initial handling: Standardize user ID, add source, replace NaN
        posts_df = posts_df.rename(columns={
            'User ID': 'User_ID'
            })
        posts_df['source'] = source
        posts_df = posts_df.fillna("")

        if replies_df is not None:
            replies_df = replies_df.rename(columns={
            'ID': 'User_ID'
            })
            
            replies_df['source'] = source
            replies_df = replies_df.fillna("")

        # keeping track of messages seen
        seen_messages = []

        # sort by message ID
        posts_df = posts_df.sort_values('Message ID', ascending=True)

        ## Build one thread per post
        for row_index, post in posts_df.iterrows():
            
            post_id = post.get("Message ID")

            # check if seen
            if post_id in seen_messages:
                continue

            single_thread = {   ##This is the outside meta, and the thread_text will contain the post + its comments
                "Message ID": post.get("Message ID"),
                "Thread_text": "",
                "URL": post.get("URL", ""),
                "Timestamp": str(post.get("Timestamp", "")),
                "User_ID": post.get("User_ID", ""),
                "source" : source
            }

            ## Add one post at a time to the threads. 
            single_thread["Thread_text"] += f"{post.get("Message_text", "")}\n--- \n\n\n"
            
            ## Get the replies for this post (trying to match the "Message ID")
            replies_ordered = []

            if replies_df is not None:
                post_replies = replies_df[replies_df["Message ID"] == post_id].sort_values('Reply ID', ascending=True)
                
                # store replies as separate records
                post_replies['is_reply'] = 1
                post_replies['is_reply_via_post'] = 0
                
                replies_records = post_replies[['Message ID', 'Reply ID', 'User_ID', 'Message_text', 'Timestamp', 'is_reply', 'is_reply_via_post']].to_dict(orient='records')
                
                # first add "normal" replies
                replies_ordered.extend(replies_records)
            
            # get replies via posts
            post_replies_internal_ = posts_df[posts_df["Reply_to_ID"] == post_id]

            # recursive function for fetching replies and replies via posts
            def get_replies_recursive(post_replies_internal, posts_df=posts_df, replies_df=replies_df):

                # look for replies via post
                if post_replies_internal.shape[0] > 0:
                    # sort by message id
                    post_replies_internal = post_replies_internal.sort_values('Message ID', ascending=True)
                    
                    # select columns
                    post_replies_internal = post_replies_internal[["Message ID", "Message_text", "URL", "Timestamp", "User_ID", "Reply_to_ID"]]
                    post_replies_internal['is_reply'] = 0
                    post_replies_internal['is_reply_via_post'] = 1

                    # iter over replies via post
                    for _, reply_via_post in post_replies_internal.iterrows():
                        
                        # get id
                        reply_via_post_id = reply_via_post.get("Message ID")

                        # adding main reply via post
                        replies_ordered.append(reply_via_post.to_dict())
                        seen_messages.append(reply_via_post_id)
                        
                        # check whether replies to reply via post - if so, add
                        if replies_df is not None:
                            reply_via_post_replies = replies_df[replies_df["Message ID"] == reply_via_post_id].sort_values('Reply ID', ascending=True)
                            if reply_via_post_replies.shape[0] > 0:
                                reply_via_post_replies['is_reply'] = 1
                                reply_via_post_replies['is_reply_via_post'] = 0
                    
                                reply_via_post_replies_records = reply_via_post_replies[['Message ID', 'Reply ID', 'User_ID', 'Message_text', 'Timestamp', 'is_reply', 'is_reply_via_post']].to_dict(orient='records')

                                replies_ordered.extend(reply_via_post_replies_records)

                        # check whether further nested in replies via posts
                        reply_via_post_replies_internal = posts_df[posts_df["Reply_to_ID"] == reply_via_post_id]

                        if reply_via_post_replies_internal.shape[0] > 0:
                            # imma gonna do it again
                            get_replies_recursive(reply_via_post_replies_internal)
                            
                
            # fetch replies recursively
            get_replies_recursive(post_replies_internal_)
                
            # combine thread             
            for reply in replies_ordered:
                single_thread["Thread_text"] += f"{reply.get("Message_text", "")} \n--- \n\n\n"

            # add replies
            single_thread["Replies"] = replies_ordered

            # append
            threads.append(single_thread)
            seen_messages.append(post_id)

        return threads, seen_messages
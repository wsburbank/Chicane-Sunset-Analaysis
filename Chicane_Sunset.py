#  Chicane Sunset
# Analysis of songs played
url = 'http://portal-api.thisisdistorted.com/xml/chicane-presents-sun-sets'

import streamlit as st
import pandas as pd
import urllib.request
import re
import plotly.express as px
import plotly.graph_objs as go
st.set_page_config(layout="wide")

@st.cache_data()
def getPodCast():
    data = urllib.request.urlopen(url).read()

    import xmltodict
    data = xmltodict.parse(data)['rss']['channel']['item']

    volume_list = [] # List of podcast volume number
    date_list = []
    mp3_list = [] # List of the mp3 url
    set_list = [] # List of the songs List in each podcast
    detail_list = []

    for pc in data:
        # Extract Volume number
        id = pc['title']
        # id = id[id.find('Vol')+4:]
        id = re.findall('(?<=Vol )[0-9]*', id)
        if len(id)==0:
            continue
        id = int(id[0])
        volume_list += [id]
        detail_list += [pc['description']]

        # Extract the published date
        date = pd.to_datetime(pc['pubDate'])
        date_list += [date]

        # Extract the MP3 link
        mp3 = pc['guid']
        mp3_list += [mp3]

        # Extract the set list
        if id == 292:
            pass
        d = pc['description']
        d = d.split('<br />')
        d = d[1:]
        playlist = []
        for s in d:
            dash_position = s.find('-')
            if dash_position<=0:
                continue
            if s.find('Sun:sets live')>0:
                continue
            artist = s[:dash_position].strip()
            song = s[dash_position+1:].strip()
            playlist += [{'artist':artist, 'song':song}]
        if id == 387:
            playlist += [{'artist':'Chicane', 'song':'Early (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Already There (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Offshore (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Lost You Somewhere (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'From Blue to Green (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Sunstroke DC (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Leaving Town (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Red Skies (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Sunstroke (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Offshore (Disco Citizens) (Evolution Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'The Drive Home (Evolution Mix)'}]
        elif id == 334:
            playlist += [{'artist':'Chicane', 'song':'Everything We Had to Leave Behind'}]
            playlist += [{'artist':'Chicane', 'song':'Hello Goodbye (Sunset Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'Circle (Beatless Mix)'}]
            playlist += [{'artist':'Chicane', 'song':'1000 More Suns'}]
            playlist += [{'artist':'Chicane', 'song':'Capricorn'}]
            playlist += [{'artist':'Chicane', 'song':'Sailing'}]
            playlist += [{'artist':'Chicane', 'song':'Now or Never'}]
            playlist += [{'artist':'Chicane', 'song':'Never Look Back'}]
            playlist += [{'artist':'Chicane', 'song':"Don't Look Down (Back Pedal Brake Replay Edit)"}]
            playlist += [{'artist':'Chicane', 'song':'Make You Stay (Back Pedal Brake Mix)'}]
        set_list += [playlist]

    set_metadata = pd.DataFrame(data = [volume_list, date_list, mp3_list, detail_list]).T
    set_metadata.columns = ['Volume', 'Date', 'mp3', 'details']

    songs = pd.DataFrame(data = [volume_list, set_list]).T
    songs.columns = ['Volume', 'Track']
    songs = songs.explode('Track', ignore_index=True)
    tracks = songs['Track'].apply(pd.Series)
    songs = pd.concat([songs, tracks], axis=1).drop(columns='Track')
    songs = songs[(songs['Volume']>5) & (songs['artist']!='')]
    songs['song'] = songs['song'].str.title()

    # Clean Artist
    songs['artist'] = songs['artist'].apply(lambda x: re.sub('^[0-9]*\.?', '', str(x)))
    songs['artist'] = songs['artist'].str.strip()
    songs['artist'] = songs['artist'].apply(lambda x: re.sub('^\.', '', str(x)))
    songs['artist'] = songs['artist'].str.title()
    songs['artist'] = songs['artist'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    songs.loc[songs['artist'].str.contains('Sigur', case=False), 'artist'] = 'Sigur Ros'
    songs.loc[songs['artist'].str.contains('Alex & Jonsi', case=False), 'artist'] = 'Jonsi & Alex'
    songs.loc[songs['artist'].str.contains('Eleven Five', case=False), 'artist'] = 'Eleven.Five'
    songs.loc[songs['artist'].str.contains('Fon Leman', case=False), 'artist'] = 'Fon.Leman'
    songs.loc[songs['artist'].str.contains('Mike Magoo', case=False), 'artist'] = 'Mike Mago'
    songs['artist'] = songs['artist'].str.strip()

    
    count = songs[['Volume', 'artist']].groupby('Volume').count()
    count.rename(columns={'artist':'num Songs'}, inplace=True)
    set_metadata = set_metadata.merge(count, how='left', on='Volume')
    return set_metadata, songs, data

set_metadata, songs, data = getPodCast()
col1, col2, col3 = st.columns([1,1,1])
# vol = st.selectbox('Select a volume', options=['ALL'] + set_metadata['Volume'].unique().tolist())
set_metadata.insert(0, "Select", False)
# col2.write(set_metadata[['Select', 'Volume', 'Date', 'num Songs']])
edited_df = col1.data_editor(
        set_metadata[['Select', 'Volume', 'Date', 'num Songs']],
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=['Volume', 'Date', 'num Songs'],
    )

d = set_metadata[edited_df['Select']]['details']
if not d.empty:
    vol = set_metadata[edited_df['Select']]['Volume'].values[0]
    col2.write(songs[songs['Volume']==vol])
    d = d.values[0]
    st.write(d)
    d = d.split('<br />')
    d = [x for x in d if x.find('-')>0]
    st.write(d)
else:
    col2.write(songs)

col1, col2, col3 = st.columns([1,1,1])
artist_histo = songs.groupby(['artist']).count()
artist_histo.rename(columns={'Volume':'Artist Count'}, inplace=True)
artist_histo.drop(columns=['song',0], inplace=True)
artist_histo.sort_values('Artist Count', ascending=False, ignore_index=False, inplace=True)
col1.write(artist_histo)

song_histo = songs.groupby(['artist','song']).count()
song_histo.rename(columns={'Volume':'Song Count'}, inplace=True)
song_histo.drop(columns=[0], inplace=True)
song_histo.sort_values('Song Count', ascending=False, ignore_index=False, inplace=True)
col2.write(song_histo)

artist_search = col1.text_input('Artist Search')
song_search = col2.text_input('Song Search')
if artist_search:
    artist_histo.reset_index(inplace=True)
    artist_histo = artist_histo[artist_histo['artist'].str.contains(artist_search, case=False)]
    artist_histo.set_index(['artist'], inplace=True)
    song_histo.reset_index(inplace=True)
    song_histo = song_histo[song_histo['artist'].str.contains(artist_search, case=False)]
    song_histo.set_index(['artist', 'song'], inplace=True)
if song_search:
    song_histo.reset_index(inplace=True)
    song_histo = song_histo[song_histo['song'].str.contains(song_search, case=False)]
    song_histo.set_index(['artist', 'song'], inplace=True)
col1.write(artist_histo)
col2.write(song_histo)

ss = st.text_input('Select Song')
if ss:
    songs = songs[songs['song'].str.contains(ss)==True]
    ss = songs.merge(set_metadata, how='left', on='Volume')
    st.write(ss)

    mp3 = st.text_input('mp3 url')
    st.write(mp3)
    if mp3:
        data = urllib.request.urlopen(mp3).read()
        st.audio(data, format='audio/mp3')
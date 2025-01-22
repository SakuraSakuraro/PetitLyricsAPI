# PetitLyrics-GET
This program is designed to search and extract song lyrics from the PetitLyrics website. It allows users to find lyrics by entering the track title, artist name, and optionally, the album name. The program supports various formats of lyrics: unsynchronized, line-synchronized, and word-synchronized.

# Main Features of the Program
1. **Search Lyrics ID:**
The program allows users to search for the lyrics ID by providing the song title, artist name, and optionally the album name. It scrapes the HTML from the petitlyrics.com website to find matching results.

2. **Fetch Lyrics by ID:**
Using the obtained lyrics ID, the program sends a request to the API to retrieve the lyrics in Base64 format. The lyrics can be:
Unsynchronized (plain text),
Synchronized line by line,
Synchronized word by word.
Decode Synchronized Lyrics:
If the lyrics are synchronized, the program decodes them using provided data. It supports decryption of LSY (encrypted) lyrics and XML-based synchronized lyrics formats.

3. **Save Lyrics to File:**
The fetched lyrics are saved in .lrc format, which is widely compatible with music players and karaoke systems.

4, **Interactive User Menu:**
Users can interact with the program via a simple text interface, entering the song title, artist name, album name, and choosing the type of lyrics (1 - unsynchronized, 2 - line-by-line sync, 3 - word-by-word sync).

# Use Case
This program is ideal for creating karaoke files or synchronized lyrics files in LRC format. It demonstrates faetures such as HTTP requests, XML parsing, Base64 decoding, and working with encryption algorithms.

# Credits
Used API request method from [EeveeSpotify by whoeevee](https://github.com/whoeevee/EeveeSpotify/blob/swift/Sources/EeveeSpotify/Lyrics/Repositories/PetitLyricsRepository.swift)

Used lyrics decode method from [petitlyric_sync_lyric_download by NingyuanWang](https://github.com/NingyuanWang/petitlyric_sync_lyric_download)

Used web search (for get by Lyrics ID) method from [mb_PetitLyricsPlugin by Netsphere Laboratories (Hisashi Horikawa)](https://github.com/netsphere-labs/mb_PetitLyricsPlugin/blob/master/mb_PetitLirycsPlugin/PetitLyrics.cs)

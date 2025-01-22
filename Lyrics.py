import base64
import requests
import xml.etree.ElementTree as ET
import io
import re
from urllib.parse import quote

def ms2mmss(ms):
    ms = int(ms)
    hs = (ms // 10) % 100
    seconds = (ms // 1000) % 60
    minutes = (ms // (1000 * 60)) % 60
    return f'[{minutes:02}:{seconds:02}.{hs:02}]'

def fetch_lyrics_id(track_title, artist, album=None):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "ja",
    })

    track_title = quote(track_title)
    artist = quote(artist)
    album = quote(album or "")

    # Search for lyrics
    search_url = f"https://petitlyrics.com/search_lyrics?title={track_title}&artist={artist}&album={album}"
    search_page = session.get(search_url).text

    try:
        start_index = search_page.index("id=\"lyrics_list\"")
        length = search_page[start_index:].index("id=\"lyrics_list_pager\"")
        lyrics_section = search_page[start_index:start_index + length]

        matches = re.findall(r'href="/lyrics/(?P<lyricId>\d+)"', lyrics_section)
        if not matches:
            return None

        # Show options if multiple matches are found
        if len(matches) > 1:
            print("Multiple lyrics found:")
            for i, match in enumerate(matches):
                print(f"{i + 1}. https://petitlyrics.com/lyrics/{match}")

            choice = int(input("Select the lyric number: ")) - 1
            lyric_id = matches[choice].strip()
        else:
            lyric_id = matches[0].strip()

    except ValueError:
        return None

    return lyric_id

def fetch_lyrics(parameters, lyrics_type_request):
    # For request
    url = "https://p0.petitlyrics.com/api/GetPetitLyricsData.php"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    client_app_id = "p1110417"

    # Form the body of the POST request
    payload = {
        "clientAppId": client_app_id,
        "lyricsType": lyrics_type_request,  # Requesting lyrics
        "terminalType": 10,
    }
    payload.update(parameters)

    # Execute the request
    response = requests.post(url, data=payload, headers=headers)

    if response.status_code != 200:
        print(f"Error executing request: {response.status_code}")
        return None, None

    # Parsing XML-resposne
    try:
        root = ET.fromstring(response.text)
        lyrics_type = root.find(".//lyricsType").text
        lyrics_data = root.find(".//lyricsData").text

        if not lyrics_data:
            print("Lyrics not found")
            return None, None

        return lyrics_type, lyrics_data

    except ET.ParseError:
        print("Error parsing XML response")
        return None, None

def lsy_decoder(lsy_base64_lyric, lyrics_text_base64):
    lyric_unsynced = base64.b64decode(lyrics_text_base64).decode("UTF-8")
    lyric_line_reader = io.StringIO(lyric_unsynced)
    lyric_string = '[00:00.00](petitlyric_lsy)\n'
    lyrics_encrypted = base64.b64decode(lsy_base64_lyric)

    protection_id = int.from_bytes(lyrics_encrypted[0x1a:0x1a+2], byteorder='little', signed=False)
    protection_key_switch_flag = bool(lyrics_encrypted[0x19])
    protection_key = protection_id

    if protection_key_switch_flag:
        masks = [
            0x3, 0xc, 0x30, 0xc0, 0x300, 0xc00, 0x3000, 0xc000
        ]
        for shift in [2, -2, 2, -2, 2, -2, -2, 2]:
            mask = masks.pop(0)
            protection_key = (protection_key & mask) | ((protection_key & mask) << shift if shift > 0 else (protection_key & mask) >> abs(shift))

    line_count = int.from_bytes(lyrics_encrypted[0x38:0x38+4], byteorder='little', signed=False)
    elapsed_time = 0

    for line_idx in range(line_count):
        time_begin_byteindex = line_idx * 2 + 0xcc
        time_raw = int.from_bytes(
            lyrics_encrypted[time_begin_byteindex:time_begin_byteindex+2],
            byteorder='little', signed=False
        )
        time_cs = time_raw ^ protection_key
        time_cs = time_cs % 65536 + 65536 * (elapsed_time // 65536)
        elapsed_time = time_cs
        time_string = ms2mmss(10 * time_cs)
        lyric_line = lyric_line_reader.readline().strip()
        lyric_string += f"{time_string}{lyric_line}\n"

    return lyric_string

def process_lyrics(parameters, lyrics_type_request):
    if lyrics_type_request == 1:
        lyrics_type, lyrics_data = fetch_lyrics(parameters, 1)
        if lyrics_data:
            lyrics = base64.b64decode(lyrics_data).decode("utf-8")
            # Removing unnecessary spaces
            cleaned_lyrics = "\n".join(line.strip() for line in lyrics.splitlines())
            # Adding a header and pseudo-synchronization
            formatted_lyrics = "(petitlyric_unsync)\n"
            for line in cleaned_lyrics.splitlines():
                formatted_lyrics += f"{line}\n"
            track_title = parameters.get("key_title", parameters.get("key_lyricsId", "unknown_track"))
        if "key_lyricsId" in parameters:
            save_lyrics_to_file(f"lyrics_{parameters['key_lyricsId']}", formatted_lyrics)
            return
        else:
            save_lyrics_to_file(parameters.get("key_title", "unknown_track"), formatted_lyrics)
            return

    lyrics_type, lyrics_data = fetch_lyrics(parameters, lyrics_type_request)

    if lyrics_type == '2':
        # If the text is synchronized line by line
        _, lyrics_text_base64 = fetch_lyrics(parameters, 1)
        if lyrics_text_base64:
            lyrics = lsy_decoder(lyrics_data, lyrics_text_base64)
            track_title = parameters.get("key_title", parameters.get("key_lyricsId", "unknown_track"))
        if "key_lyricsId" in parameters:
            save_lyrics_to_file(f"lyrics_{parameters['key_lyricsId']}", lyrics)
            return
        else:
            save_lyrics_to_file(parameters.get("key_title", "unknown_track"), lyrics)
            return

    elif lyrics_type == '3':
        # If the text is synchronized word by word
        lyrics_petitlyricform = base64.b64decode(lyrics_data).decode("UTF-8")
        lyrics_tree = ET.fromstring(lyrics_petitlyricform)
        lyric_string = '[00:00.00](petitlyric_wsy)\n'
        for line in lyrics_tree.findall('line'):
            timepoint = line.find('word/starttime').text
            lyric_line = line.find('linestring').text or ''
            lyric_string += f"{ms2mmss(timepoint)}{lyric_line}\n"
            track_title = parameters.get("key_title", parameters.get("key_lyricsId", "unknown_track"))
        if "key_lyricsId" in parameters:
            save_lyrics_to_file(f"lyrics_{parameters['key_lyricsId']}", lyric_string)
            return
        else:
            save_lyrics_to_file(parameters.get("key_title", "unknown_track"), lyric_string)
        return

    print("Lyrics not found or not supported")


def save_lyrics_to_file(track_title, lyrics):
    filename = f"{track_title}.lrc"
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(lyrics)
        print(f"Lyrics saved to file: {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")

def main():
    choice = input("Do you want to search for the lyrics ID? (Y - yes/N - no): ").strip().lower()

    if choice in ['y', 'Y']:
        track_title = input("Enter the track name: ").strip()
        artist = input("Enter the artist name: ").strip()
        album = input("Enter the album name (optional): ").strip()

        lyrics_id = fetch_lyrics_id(track_title, artist, album)
        if not lyrics_id:
            print("Lyrics ID not found")
            return

        print(f"Found lyrics ID: {lyrics_id}")

        print("Select the type of lyrics:")
        print("1. Unsynchronized (Type 1)")
        print("2. Synchronized line by line (Type 2)")
        print("3. Synchronized word by word (Type 3)")
        choice = input("Enter 1, 2, or 3: ").strip()

        if choice == '1':
            lyrics_type_request = 1
        elif choice == '2':
            lyrics_type_request = 2
        elif choice == '3':
            lyrics_type_request = 3
        else:
            print("Invalid choice. Exiting the program")
            return

        process_lyrics({"key_lyricsId": lyrics_id}, lyrics_type_request)

    else:
        artist = input("Enter the artist name: ").strip()
        track_title = input("Enter the track name: ").strip()
        album = input("Enter the album name (optional): ").strip()

        print("Select the type of lyrics:")
        print("1. Unsynchronized (Type 1)")
        print("2. Synchronized line by line (Type 2)")
        print("3. Synchronized word by word (Type 3)")
        choice = input("Enter 1, 2, or 3: ").strip()

        if choice == '1':
            lyrics_type_request = 1
        elif choice == '2':
            lyrics_type_request = 2
        elif choice == '3':
            lyrics_type_request = 3
        else:
            print("Invalid choice. Exiting the program")
            return

        process_lyrics({"key_artist": artist, "key_title": track_title, "key_album": album}, lyrics_type_request)

if __name__ == "__main__":
    main()

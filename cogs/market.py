from discord.ext import commands
import sqlite3
from bs4 import BeautifulSoup
import requests
import os
from datetime import datetime

marketDatabase = sqlite3.connect('market.db')
marketCursor = marketDatabase.cursor()
marketCursor.execute("CREATE TABLE IF NOT EXISTS Cards(カード STRING, カードイメージ STRING, レアリティ STRING, カテゴリ STRING, 色 STRING, レベル INT, コスト INT, パワー INT, ソウル INT, トリガー STRING, 特徴 STRING)")
marketCursor.execute("CREATE TABLE IF NOT EXISTS PriceHistory (カード STRING, カードショップ STRING, datetime STRING, 値段 INT)")

triggerDict = {
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_0.png" : "empty_trigger.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_1.png" : "trigger.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_I.png" : "choice.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_1A.png" : "wind.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_1E.png" : "shot.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_F.png" : "goldbar.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_B.png" : "bag.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_1G.png" : "pants.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_D.png" : "book.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_C.png" : "door.png",
    "https://cdn.yuyu-tei.jp/images/icon/ws/icon_tri_1H.png" : "standby.png"    
               }

def createDir(directory):
    try:
        os.mkdir(directory)
        print(f"Directory '{directory}' created successfully.")
    except FileExistsError:
        print(f"Directory '{directory}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{directory}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

def downloadImg(imgURL, savePath, fileName):
    
    response = requests.get(imgURL)

    fullPath = os.path.join(savePath, fileName)

    if response.status_code == 200:
        with open(fullPath, 'wb') as file:
            file.write(response.content)
            print(f"Image downloaded successfully to {savePath}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")

def directorySetup(*args):
    # lets set up the necessary directories
    for dir in args:
        createDir(dir)


def getCardInfo(cardTag, rarity):

    imgDir = "WeissSchwarzMatchmakingBot/images"
    triggerDir = "WeissSchwarzMatchmakingBot/images/triggers"
    cardDir = "WeissSchwarzMatchmakingBot/images/cards"
    directorySetup(imgDir, triggerDir, cardDir)

    # search for the card on yuyutei
    url = "https://yuyu-tei.jp/sell/ws/s/search?search_word=" + cardTag

    # getting the page
    page = requests.get(url)

    # BeautifulSoup object 
    soup = BeautifulSoup(page.text, 'html.parser')

    # selecting this thing because it has the info we need
    cardOptions = soup.select('div.position-relative.product-img')

    # empty string for the needed card which we will fill when we find the card we need
    neededCard = ""

    # iterate through the cards available, when we find the correct rarity, we set that as the needed card
    for card in cardOptions:
        
        imageTag = card.find('img')

        # split the alt text so we can check rarity
        altText = imageTag['alt'].split(" ")

        # need to ensure the alt text has at least 2 elements
        if len(altText) >= 2:
            # altText[1] should have the rarity of the card, if it the correct rarity, we set the needed card and break
            if rarity == altText[1]:
                neededCard = card
                break

    if neededCard == "":
        print("Something is wrong")
        return()

    # the parent of this has the link to the page of the card we wanted to find (in the href)
    cardParent = neededCard.find_parent()
    link = cardParent.get('href')

    # now that we have the link we need, lets set get the page and set up the new BeautifulSoup object
    page = requests.get(link)
    soup = BeautifulSoup(page.text, 'html.parser')

    # creating dictionary to hold our data before adding it do db hypothetically
    cardDict = {}

    # get cost of card
    円 = soup.select_one('h4.fw-bold.d-inline-block').text[:-1].strip()

    # get card img
    cardImg = soup.select_one('img.vimg')
    cardImgLink = cardImg['src']

    # need to make card tag suitable for being a filename
    cardFileName = cardTag.replace("/", "_")
    cardFileName = cardFileName + ".jpg"

    # create full path to card directory
    fullPath = os.path.join(cardDir, cardFileName)

    # checking if the image is already in the card directory, download it if not
    if os.path.isfile(fullPath):
        print(f"The file '{cardFileName}' already exists in the directory")
    else:
        downloadImg(cardImgLink, cardDir, cardFileName)

    # add card tag and location of image to dictionary
    cardDict.update({'カード' : cardTag})
    cardDict.update({'カードイメージ' : cardDir + '/' + cardFileName})

    # get datetime for price
    currDatetime = datetime.now().replace(microsecond=0)

    # adding important info to the dictionary
    cardDict.update({"カードショップ" : "遊々亭"})
    cardDict.update({"値段" : int(円)})
    cardDict.update({"datetime" : str(currDatetime)})
    cardDict.update({"レアリティ" : rarity})


    # get the information about the card from yuyutei (like type, color, level, etc.)
    # we only need to do this if the card is not in the database, but we don't have database compatibility yet
    rawCardClassif = soup.select("th.text-primary.w-25.border-end-0")
    rawCardInfo = soup.select('td.text-dark.w-25.border-start-0')

    # size of these lists is the same when it is a character, but not when it is a climax or event, so we are fixing for that
    if rawCardInfo[0].text.strip() == "クライマックス" or rawCardInfo[0].text.strip() == "イベント":
        rawCardInfo.pop()

    # length of raw card classifications and raw card information should be the same
    if len(rawCardClassif) == len(rawCardInfo):
        # iterate through the lists and add them to the dictionary
        for x in range(len(rawCardClassif)):
            cardDict.update({rawCardClassif[x].text.strip() : rawCardInfo[x].text.strip()})
            
            # some of the stuff added needs to become ints, so yeah
            if rawCardClassif[x].text.strip() == "レベル" or rawCardClassif[x].text.strip() == "コスト" or rawCardClassif[x].text.strip() == "パワー" or rawCardClassif[x].text.strip() == "ソウル":
                cardDict.update({rawCardClassif[x].text.strip() : int(rawCardInfo[x].text.strip())})

            # Yuyutei has the trigger icon as an image so we need to find the link and download it if we haven't already
            if rawCardClassif[x].text.strip() == "トリガー":
                # gettin da link
                triggerImglink = rawCardInfo[x].find('img')['src']
                # we check if this link is in the dictionary of all the links, if it isn't then something is wrong
                if triggerImglink in triggerDict:
                    triggerFileName = triggerDict.get(triggerImglink)
                else:
                    print("This link isn't in the trigger dictionary")
                    return()
                # get the full path to the trigger directory with the file name and check if it is in the folder, if not download it
                fullPath = os.path.join(triggerDir, triggerFileName)
                if os.path.isfile(fullPath):
                    print(f"The file '{triggerFileName}' already exists in the directory")
                else:
                    downloadImg(triggerImglink, triggerDir, triggerFileName)
                # update trigger to the desired image location
                cardDict.update({rawCardClassif[x].text.strip() : triggerDir + '/' + triggerFileName})
    else:
        print("These lists should be the same size, something went wrong")
        return()
    
    return cardDict

class market(commands.Cog):
    
    def __init__(self, client):
        self.client = client
    
    @commands.command(pass_context = True)
    async def check(self, ctx, cardTag, rarity):
        
        neededDict = getCardInfo(cardTag, rarity)
        # needed variables for Cards table and overall for embed
        cardImgPath = neededDict.get("カードイメージ")
        cardCategory = neededDict.get("カテゴリ")
        cardColor = neededDict.get("色")
        cardLevel = neededDict.get("レベル")
        cardCost = neededDict.get("コスト")
        cardPower = neededDict.get("パワー")
        cardSoul = neededDict.get("ソウル")
        triggerImgPath = neededDict.get("トリガー")
        cardTraits = neededDict.get("特徴")
        # needed for PriceHistory table specifically
        cardShop = neededDict.get("カードショップ")
        cardDatetime = neededDict.get("datetime")
        cardPrice = neededDict.get("値段")

        query = "SELECT EXISTS(SELECT 1 FROM Cards WHERE カード=?)"

        marketCursor.execute(query, (cardTag,))

        cardTuple = marketCursor.fetchone()
        cardExists = cardTuple[0]

        if cardExists == 1:
            print(f"{cardTag} is already in the database")
        else:
            query = "INSERT INTO Cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            values = (cardTag, cardImgPath, rarity, cardCategory, cardColor, cardLevel, cardCost, cardPower, cardSoul, triggerImgPath, cardTraits)
            marketCursor.execute(query, values)
            marketDatabase.commit()
        
        query = "INSERT INTO PriceHistory VALUES (?, ?, ?, ?)"
        values = (cardTag, cardShop, cardDatetime, cardPrice)
        marketCursor.execute(query, values)
        marketDatabase.commit()

async def setup(client):
    await client.add_cog(market(client))  
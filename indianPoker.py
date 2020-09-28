import random
import os
import sys

import pygame

from pygame.locals import *
pygame.font.init()
pygame.mixer.init()

screen = pygame.display.set_mode((820, 480))
clock = pygame.time.Clock()

def imageLoad(name, card):
    # 이미지 불러오기 용. 
    # 오류 발생 시 열 수 없는 파일명을 알려줌
    
    if card == 1:
        fullname = os.path.join("images/cards/", name)
    else: fullname = os.path.join('images', name)
    
    try:
        image = pygame.image.load(fullname)
    except (pygame.error, message):
        print ('이미지 불러오기 실패:', name)
        raise (SystemExit, message)
    image = image.convert()
    
    return image, image.get_rect()
        
def soundLoad(name):
    # 클릭 시 소리 불러오기
    
    fullName = os.path.join('sounds', name)
    try: sound = pygame.mixer.Sound(fullName)
    except (pygame.error, message):
        print ('사운드 불러오기 실패:', name)
        raise (SystemExit, message)
    return sound

def display(font, sentence):
    # 화면 하단에 현재 진행사항에 대한 텍스트 출력
    
    displayFont = pygame.font.Font.render(font, sentence, 1, (255,255,255), (0,0,0)) 
    return displayFont

def playClick():
    # 누를경우 나는 사운드 설정
    clickSound = soundLoad("click2.wav")
    clickSound.play()

def mainGame():
    # 전체 게임 로직 설정
    
    def gameOver():
        # 베팅 자본금이 다 떨어질 경우
        
        while 1:
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit()
                if event.type == KEYDOWN and event.key == K_ESCAPE:
                    sys.exit()

            screen.fill((0,0,0))
            
            oFont = pygame.font.Font(None, 50)
            displayFont = pygame.font.Font.render(oFont, "Game over!", 1, (255,255,255), (0,0,0)) 
            screen.blit(displayFont, (125, 220))
            
            pygame.display.flip()
            
    ######## 덱 관련 함수 ########
    def shuffle(deck):
        # Fisher-Yates Shuffle 알고리즘을 통해 덱을 섞음.

        n = len(deck) - 1
        while n > 0:
            k = random.randint(0, n)
            deck[k], deck[n] = deck[n], deck[k]
            n -= 1

        return deck       
                        
    def createDeck():
        # 덱 생성 (스페이드 에이스부터 10까지)

        deck = []
        values = range(0,10)
        for x in values:
            spades = str(x) + "_of_spades"
            deck.append(spades)
            deck.append(spades)
        return deck

    def returnFromDead(deck, deadDeck):
        # 덮어진 덱이 전부 사용될 경우 다시 셔플을 시작

        for card in deadDeck:
            deck.append(card)
        del deadDeck[:]
        deck = shuffle(deck)

        return deck, deadDeck
        
    def deckDeal(deck, deadDeck):
        # 1장씩 나눠줌

        deck = shuffle(deck)
        dealerHand, playerHand = [], []

        cardsToDeal = 2

        while cardsToDeal > 0:
            if len(deck) == 0:
                deck, deadDeck = returnFromDead(deck, deadDeck)

            # deal the first card to the player, second to dealer, 3rd to player, 4th to dealer, based on divisibility (it starts at 4, so it's even first)
            if cardsToDeal % 2 == 0: playerHand.append(deck[0])
            else: dealerHand.append(deck[0])
            
            del deck[0]
            cardsToDeal -= 1
            
        return deck, deadDeck, playerHand, dealerHand

    def checkValue(hand):
        # 손패의 크기 합을 확인

        totalValue = 0

        for card in hand:
            value = card[0:1]

            # 1~10까지의 카드 값 입력    
            if value == '0': value = 10
            else: value = int(value)

            totalValue += value

        return totalValue

    def endRound(deck, playerHand, dealerHand, deadDeck, funds, moneyGained, moneyLost, cards, cardSprite):
        # 라운드 종료 시 손패 크기 비교

        # 딜러의 뒷면 카드패 공개
        cards.empty()
        # 딜러가 아닌 플레이어 쪽으로 위치조정 필요(이벤트의 경우에만)
        dCardPos = (50, 70)

        for x in dealerHand:
            card = cardSprite(x, dCardPos)
            dCardPos = (dCardPos[0] + 80, dCardPos [1])
            cards.add(card)

        # 지닌 손패 사용완료 덱으로 이동
        for card in playerHand:
            deadDeck.append(card)
        for card in dealerHand:
            deadDeck.append(card)
        del playerHand[:]
        del dealerHand[:]

        # 결과에 따른 베팅금 분배
        funds += moneyGained
        funds -= moneyLost
        
        textFont = pygame.font.Font(None, 28)
        
        if funds <= 0:
            gameOver()  
        
        roundEnd = 1

        return deck, playerHand, dealerHand, deadDeck, funds, roundEnd 
        
    def compareHands(deck, deadDeck, playerHand, dealerHand, funds, bet, cards, cardSprite, betted):
        # 플레이어나 딜러가 라운드 시작 혹은 종료시 블랙잭을 가진 경우 호출.
        # 블랙잭 게임 룰에 따라 누가 승자인지 확인해줌

        textFont = pygame.font.Font(None, 28)
        moneyGained = 0
        moneyLost = 0

        dealerValue = checkValue(dealerHand)
        playerValue = checkValue(playerHand)

        if playerValue > dealerValue:
            # 플레이어 승
            moneyGained = betted
            deck, playerHand, dealerHand, deadDeck, funds, roundEnd = endRound(deck, playerHand, dealerHand, deadDeck, funds, bet, 0, cards, cardSprite)
            displayFont = display(textFont, "+ $%.2f." %(bet))
        elif playerValue == dealerValue:
            # 동률
            deck, playerHand, dealerHand, deadDeck, funds, roundEnd = endRound(deck, playerHand, dealerHand, deadDeck, funds, 0, 0, cards, cardSprite)
            displayFont = display(textFont, "draw!")
        elif dealerValue > 21 and playerValue <= 21:
            # 플레이어 승
            deck, playerHand, dealerHand, deadDeck, funds, roundEnd = endRound(deck, playerHand, dealerHand, deadDeck, funds, bet, 0, cards, cardSprite)
            displayFont = display(textFont, "+ $%.2f." %(bet))
        else:
            # 이외의 경우에는 딜러 승 처리
            deck, playerHand, dealerHand, deadDeck, funds, roundEnd = endRound(deck, playerHand, dealerHand, deadDeck, funds, 0, bet, cards, cardSprite)
            displayFont = display(textFont, "- $%.2f." %(bet))

        return deck, deadDeck, roundEnd, funds, displayFont
    ########  ########  
    
    ######## 이미지 객체 생성 ##########
    class cardSprite(pygame.sprite.Sprite):
        # 숫자 카드 이미지를 표현하는 객체
        def __init__(self, card, position):
            pygame.sprite.Sprite.__init__(self)
            cardImage = card + ".png"
            self.image, self.rect = imageLoad(cardImage, 1)
            self.position = position
        def update(self):
            self.rect.center = self.position
            
    class betButton(pygame.sprite.Sprite):
        # hit 버튼
        
        def __init__(self):
            pygame.sprite.Sprite.__init__(self)
            self.image, self.rect = imageLoad("bet-grey.png", 0)
            self.position = (663,285) 
            
        def update(self, mX, mY, roundEnd, funds, bet, displayFont, betted):
            # 버튼을 누를 경우의 행동 방식(라운드 종료 상태 아닌 경우에만, 카드 추가해줌)

            if roundEnd == 0: self.image, self.rect = imageLoad("bet.png", 0)
            else: self.image, self.rect = imageLoad("bet-grey.png", 0)

            self.position = (735, 400)
            self.rect.center = self.position

            if self.rect.collidepoint(mX, mY) == 1:
                if roundEnd == 0 and funds>=betted+bet:
                    betted = betted + bet
                    playClick()


            return deck, deadDeck, playerHand, pCardPos, click, betted
            
    class standButton(pygame.sprite.Sprite):
        # stand 버튼
        
        def __init__(self):
            pygame.sprite.Sprite.__init__(self)
            self.image, self.rect = imageLoad("stand-grey.png", 0)
            self.position = (735, 365)
            
        def update(self, mX, mY, deck, deadDeck, playerHand, dealerHand, cards, pCardPos, roundEnd, cardSprite, funds, bet, displayFont, betted):
            # stand 시 이벤트 발생
            
            if roundEnd == 0: self.image, self.rect = imageLoad("stand.png", 0)
            else: self.image, self.rect = imageLoad("stand-grey.png", 0)
            
            self.position = (735, 365)
            self.rect.center = self.position
            
            if self.rect.collidepoint(mX, mY) == 1:
                if roundEnd == 0: 
                    playClick()
                    deck, deadDeck, roundEnd, funds, displayFont = compareHands(deck, deadDeck, playerHand, dealerHand, funds, bet, cards, cardSprite)
                    betted = 0.00

            return deck, deadDeck, roundEnd, funds, playerHand, deadDeck, pCardPos, displayFont, betted

    class dealButton(pygame.sprite.Sprite):
        # 라운드 종료 상태 시 게임을 시작하고자 할 때 누르는 일종의 게임 시작버튼
        
        def __init__(self):
            pygame.sprite.Sprite.__init__(self)
            self.image, self.rect = imageLoad("deal.png", 0)
            self.position = (735, 450)

        def update(self, mX, mY, deck, deadDeck, roundEnd, cardSprite, cards, playerHand, dealerHand, dCardPos, pCardPos, displayFont, playerCards, click, handsPlayed):
            # 버튼이 눌렸을때 roundEnd의 값이 0이 아닐 경우, deckDeal 함수를 호출해서, 딜러와 플레이어에게 카드를 전해줌
            # 이후 전달된 카드에 맞는 이미지 객체를 생성해줌 (cardSprite 클래스). 라운드 종료상태거나 승자가 결정난 경우에만 활성화
            
            # 설명 텍스트 창 비움
            textFont = pygame.font.Font(None, 28)
            
            if roundEnd == 1: self.image, self.rect = imageLoad("deal.png", 0)
            else: self.image, self.rect = imageLoad("deal-grey.png", 0)
            
            self.position = (735, 450)
            self.rect.center = self.position


            if self.rect.collidepoint(mX, mY) == 1:
                if roundEnd == 1 and click == 1:
                    playClick()
                    displayFont = display(textFont, "")
                    
                    cards.empty()
                    playerCards.empty()
                    
                    deck, deadDeck, playerHand, dealerHand = deckDeal(deck, deadDeck)

                    dCardPos = (50, 70)
                    pCardPos = (540,370)

                    # 플레이어 카드 이미지 객체 생성 (cardSprite 클래스), 초기에 두개가 배부되서 for문 사용
                    for x in playerHand:
                        card = cardSprite(x, pCardPos)
                        pCardPos = (pCardPos[0] - 80, pCardPos [1])
                        playerCards.add(card)
                    
                    # 딜러 카드 이미지 객체 생성 (cardSprite 클래스)
                    faceDownCard = cardSprite("back", dCardPos)
                    dCardPos = (dCardPos[0] + 80, dCardPos[1])
                    cards.add(faceDownCard)

                    card = cardSprite(dealerHand [0], dCardPos)
                    cards.add(card)
                    roundEnd = 0
                    click = 0
                    handsPlayed += 1
                    
            return deck, deadDeck, playerHand, dealerHand, dCardPos, pCardPos, roundEnd, displayFont, click, handsPlayed
            
            
    class betButtonUp(pygame.sprite.Sprite):
        # 베팅금 올리기
        
        def __init__(self):
            pygame.sprite.Sprite.__init__(self)
            self.image, self.rect = imageLoad("up.png", 0)
            self.position = (710, 255)
            
        def update(self, mX, mY, bet, funds, click, roundEnd):
            self.image, self.rect = imageLoad("up.png", 0)
            
            self.position = (710, 255)
            self.rect.center = self.position
            
            if self.rect.collidepoint(mX, mY) == 1 and click == 1:
                playClick()

                if bet < funds:
                    bet += 10.0
                    # 베팅금 상승이 5로 떨어지지 않는 경우를 확인
                    # 블랙잭일 경우 1.5배로 돌려받는 경우가 있어 자본금이 5로 안 떨어지는 경우가 있음
                    if bet % 10 != 0:
                        while bet % 10 != 0:
                            bet -= 1

                click = 0
            
            return bet, click
            
    class betButtonDown(pygame.sprite.Sprite):
        # 베팅금 낮추는 용도
        
        def __init__(self):
            pygame.sprite.Sprite.__init__(self)
            self.image, self.rect = imageLoad("down.png", 0)
            self.position = (710, 255)
            
        def update(self, mX, mY, bet, click, roundEnd):  
            self.image, self.rect = imageLoad("down.png", 0)
        
            self.position = (760, 255)
            self.rect.center = self.position
            
            if self.rect.collidepoint(mX, mY) == 1 and click == 1:
                playClick()
                if bet > 10:
                    bet -= 10.0
                    if bet % 10 != 0:
                        while bet % 10 != 0:
                            bet += 1
                    
                click = 0
            
            return bet, click
    ######  ######
         
    ###### 객체 선언 항목 ######
    # 상황 안내용 텍스트에 대한 설정(값 X, 폰트 크기 28 설정)
    textFont = pygame.font.Font(None, 28)

    # 배경화면 이미지 설정
    background, backgroundRect = imageLoad("bjs.png", 0)
    
    # 딜러 카드의 이미지 스프라이트 그룹 설정
    cards = pygame.sprite.Group()
    # 플레이어 카드의 이미지 스프라이트 그룹 설정
    playerCards = pygame.sprite.Group()

    # 각종 버튼에 대한 객체 설정(위의 클래스 적용)
    bbU = betButtonUp()
    bbD = betButtonDown()
    standButton = standButton()
    dealButton = dealButton()
    betButton = betButton()
    
    # 버튼 스프라이트 그룹화
    buttons = pygame.sprite.Group(bbU, bbD, betButton, standButton, dealButton)

    # 20개 카드덱 생성
    deck = createDeck()
    # 사용된 카드를 모아놓을 장소
    deadDeck = []

    playerHand, dealerHand, dCardPos, pCardPos = [],[],(),()
    mX, mY = 0, 0
    click = 0

    # 베팅 시작금과 기본 베팅금 설정
    funds = 5000.00
    bet = 10.00
    betted = 0.00

    handsPlayed = 0

    # 0 = 라운드 진행 상태, 1 = 라운드 종료 상태
    roundEnd = 1
    
    # 전체 프로그램에 대한 선언을 위한 변수
    # 코드 실행 이후 0으로 설정되며 이후 사용되지 않음
    firstTime = 1
    ######  ########
    
    ###### MAIN #######
    while 1:
        screen.blit(background, backgroundRect)
        
        if bet > funds:
            # 가진 자본금에 비해 사용자의 베팅금이 커질 경우 소지 자본금과 동일한 값으로 설정하게 함
            bet = funds
        
        if roundEnd == 1 and firstTime == 1:
            # 라운드가 한번도 실행되지 않은 경우, 하단의 레이블에 내용을 출력
            displayFont = display(textFont, "화살표로 베팅금을 설정하고 Deal 버튼을 눌러 게임을 시작합니다")
            firstTime = 0
            
        # 현재 소지금과 베팅금, 진행된 라운드 수에 대한 레이블 설정 부분
        screen.blit(displayFont, (10,444))
        hpFont = pygame.font.Font.render(textFont, "Round: %i " %(handsPlayed), 1, (255,255,255), (0,0,0))
        screen.blit(hpFont, (663, 180))
        fundsFont = pygame.font.Font.render(textFont, "Funds: $%.2f" %(funds), 1, (255,255,255), (0,0,0))
        screen.blit(fundsFont, (663,205))
        betFont = pygame.font.Font.render(textFont, "Bet: $%.2f" %(bet), 1, (255,255,255), (0,0,0))
        screen.blit(betFont, (663,285))
        bettedFont = pygame.font.Font.render(textFont, "Betted: $%.2f" %(betted), 1, (255,255,255), (0,0,0))
        screen.blit(bettedFont, (663,310))

        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    mX, mY = pygame.mouse.get_pos()
                    click = 1
            elif event.type == MOUSEBUTTONUP:
                mX, mY = 0, 0
                click = 0

        # deal 버튼 
        deck, deadDeck, playerHand, dealerHand, dCardPos, pCardPos, roundEnd, displayFont, click, handsPlayed = dealButton.update(mX, mY, deck, deadDeck, roundEnd, cardSprite, cards, playerHand, dealerHand, dCardPos, pCardPos, displayFont, playerCards, click, handsPlayed)   
        # hit 버튼
        deck, deadDeck, playerHand, pCardPos, click, betted = betButton.update(mX, mY, roundEnd, funds, bet, displayFont, betted)
        # stand 버튼
        deck, deadDeck, roundEnd, funds, playerHand, deadDeck, pCardPos, displayFont, betted = standButton.update(mX, mY,   deck, deadDeck, playerHand, dealerHand, cards, pCardPos, roundEnd, cardSprite, funds, bet, displayFont, betted)
        # Bet 버튼
        bet, click = bbU.update(mX, mY, bet, funds, click, roundEnd)
        bet, click = bbD.update(mX, mY, bet, click, roundEnd)
        
        buttons.draw(screen)
         
        if len(cards) != 0:
            playerCards.update()
            playerCards.draw(screen)
            cards.update()
            cards.draw(screen)

        pygame.display.flip()

if __name__ == "__main__":
    mainGame()

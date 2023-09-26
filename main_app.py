import main_car
import main_house
import main_secondHand
import time

if __name__ == '__main__':
    while True:
        main_house.run()
        main_car.run()
        main_secondHand.run()
        print("main_app called @", time.ctime())
        time.sleep(5)  # 1000 = 16min, 10000 seconds = 2.7 hours


from experta import *

VIEW = False

problems = []


class PowerSupply(Fact):
    pass


class PSU(Fact):
    pass


class Screen(Fact):
    pass


class Sound(Fact):
    pass


class Common(Fact):
    pass


class HDD(Fact):
    pass


class Info(Fact):
    pass


def calculate_cf(cf1, cf2):
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1 + cf1)
    return (cf1 + cf2) / (1 - min(abs(cf1), abs(cf2)))


class Knowledge(KnowledgeEngine):

    def ask(self, q):
        ans = int(input(q))
        if ans == 1:
            cf_user = float(input("How often? "))
            return cf_user
        return 0

    @DefFacts()
    def defacts(self):
        yield HDD(name="HDD", CF=0, symptoms={'missingMBR': 0.6, 'replacement': 0.3, 'bad_sector': 0.5}, done=0)
        yield Screen(name="Screen", CF=0, symptoms={'stuttering': 0.5, 'flickering': 0.3, 'led_panel': 0.4}, done=0)
        yield Sound(name="Sound", CF=0,
                    symptoms={'no_sound_driver': 0.7, 'no_sound_hardware': 0.5, 'clink': 0.4, 'card_problem': 0.3},
                    done=0)
        yield PSU(name="PSU", CF=0, symptoms={'click_fault': 0.8, 'connection_pin': 0.3}, done=0)
        yield PowerSupply(name="Power Supply", CF=0, symptoms={'fan_dust': 0.4, 'fan_malfunction': 0.5,
                                                               'overheat': 0.3, 'not_starting': 0.6}, done=0)
        # Test #
        # yield Info(click_fault=0.3,connection_pin=0.6)
        # yield Info(fan_dust=0.1,overheat=0,not_starting=0,fan_malfunction=0.4)
        # yield Info(not_booting=0.8,clicky=0.5,heating=0.1,slow_file_access=0.5,sys_crash=0)
        # yield Info(stuttering=0.2,flickering=0.7,led_panel=0)
        # yield Info(no_sound=0.6,clinking=0.3)

    @Rule(NOT(Info(click_fault=W(), connection_pin=W())), salience=12)
    def psu(self):
        print("PSU:")
        self.declare(Info(click_fault=self.ask("Computer not turns on?"),
                          connection_pin=self.ask("psu light on but computer not starts?")))

    @Rule(NOT(Info(fan_dust=W(), overheat=W(),fan_malfunction=W(), not_starting=W())), salience=11)
    def powr(self):
        print("Power Supply")
        self.declare(Info(not_starting=self.ask("computer not starting?"),
                          fan_dust=self.ask("hearing loud sound on working?"),
                          fan_malfunction=self.ask("hearing cracking sound?"),
                          overheat=self.ask("smelling burn?")))

    @Rule(NOT(Info(not_booting=W(), clicky=W(), heating=W(), slow_file_access=W(), sys_crash=W())), salience=11)
    def start(self):
        print("HDD:")
        self.declare(Info(not_booting=self.ask("System is not Booting?"), clicky=self.ask("Hearing clicks sound?"),
                          heating=self.ask("Overheating?"), slow_file_access=self.ask("slow file access?"),
                          sys_crash=self.ask("System crashing?")))

    @Rule(NOT(Info(stuttering=W(),flickering=W(),led_panel=W())),salience=10)
    def start2(self):
        print("Screen:")
        self.declare(Info(stuttering=self.ask("Screen stuttering?"), flickering=self.ask("Screen Flickering?"),
                          led_panel=self.ask("black or colored lines?")))

    @Rule(NOT(Info(no_sound=W(),clinking=W())), salience=9)
    def start3(self):
        print("Sound:")
        self.declare(Info(no_sound=self.ask("no sound?"), clinking=self.ask("sound clinking?")))

    ############# HDD #############
    @Rule(Info(not_booting=MATCH.not_booting, clicky=MATCH.clicky,
               heating=MATCH.heating, slow_file_access=MATCH.slow_file_access, sys_crash=MATCH.sys_crash)
        , AS.fact << HDD(CF=MATCH.CF, symptoms=MATCH.symptoms, done=0), salience=8)
    def hdd(self, symptoms, clicky, not_booting, slow_file_access, sys_crash, heating, fact):
        cf_mbr = symptoms['missingMBR'] * not_booting
        cf_Replace = symptoms['replacement'] * heating + symptoms['replacement'] * sys_crash + symptoms[
            'replacement'] * clicky
        cf_badsec = symptoms['bad_sector'] * slow_file_access + symptoms['bad_sector'] * sys_crash
        solution = max(cf_Replace, cf_mbr, cf_badsec)
        if solution != 0:
            print("HDD solution:")
            if solution == cf_mbr:
                print(" Missing MBR", solution)
            elif solution == cf_badsec:
                print(" Bad Sector", solution)
            else:
                print(" Replacement", solution)
        cf1 = calculate_cf(cf_mbr, cf_Replace)
        cf_final = calculate_cf(cf1, cf_badsec)
        self.modify(fact, CF=cf_final, done=1)

    ########### SCREEN ############
    @Rule(Info(stuttering=MATCH.stuttering, flickering=MATCH.flickering, led_panel=MATCH.led_panel),
          AS.fact << Screen(CF=0, symptoms=MATCH.symptoms, done=0), salience=7)
    def screen(self, stuttering, flickering, symptoms, led_panel, fact):
        cf_stut = symptoms['stuttering'] * stuttering
        cf_flick = symptoms['flickering'] * flickering
        cf_led = symptoms['led_panel'] * led_panel
        solution = max(cf_flick, cf_led, cf_stut)
        if solution != 0:
            print("Screen solution:")
            if solution == cf_stut:
                print(" change cable")
            elif solution == cf_led:
                print(" change screen panel")
            else:
                print(" change screen")

        cf_final = calculate_cf(cf_flick, cf_stut)
        cf_final = calculate_cf(cf_final, cf_led)
        self.modify(fact, CF=cf_final, done=1)

    ########## Sound ###########

    @Rule(Info(no_sound=MATCH.no_sound, clinking=MATCH.clinking),
          AS.fact << Sound(CF=MATCH.CF, symptoms=MATCH.symptoms, done=0), salience=6)
    def sound(self, no_sound, symptoms, clinking, fact):
        cf_sound = symptoms['no_sound_driver'] * no_sound + symptoms['no_sound_hardware'] * no_sound + symptoms[
            'card_problem'] * no_sound
        cf_clink = symptoms['clink'] * clinking + symptoms['no_sound_driver'] * clinking
        solution = max(cf_sound, cf_clink)
        if solution != 0:
            print("Sound solution:")
            if solution == cf_sound:
                print("try re-install sound driver. if problem persist change card sound", cf_sound)
            else:
                print("change speakers", cf_clink)
        cf_final = calculate_cf(cf_clink, cf_sound)
        self.modify(fact, CF=cf_final, done=1)

    ########## PSU ############
    @Rule(Info(click_fault=MATCH.click_fault, connection_pin=MATCH.connection_pin), AS.fact <<
          PSU(CF=MATCH.CF, symptoms=MATCH.symptoms, done=0), salience=4)
    def psurule(self, click_fault, symptoms, connection_pin, fact):
        cf_click = click_fault * symptoms['click_fault']
        cf_pin = connection_pin * symptoms['connection_pin']
        solution = max(cf_pin, cf_click)
        if solution != 0:
            print("PSU solution", solution)
            if solution == cf_click:
                print("change psu button")
            else:
                print("change connection pin to mother board")
        cf_final = calculate_cf(cf_click, cf_pin)
        self.modify(fact, CF=cf_final, done=1)

    ######## POWER SUPPLY #########
    @Rule(Info(fan_dust=MATCH.fan_dust, fan_malfunction=MATCH.fan_malfunction, overheat=MATCH.overheat,
               not_starting=MATCH.not_starting), AS.fact << PowerSupply(CF=MATCH.CF, symptoms=MATCH.symptoms, done=0),
          salience=5)
    def powerrule(self, fan_dust, fan_malfunction, overheat, not_starting, fact, symptoms):
        cf_dust = fan_dust * symptoms['fan_dust']
        cf_malfunction = fan_malfunction * symptoms['fan_malfunction']
        cf_overheat = overheat * symptoms['overheat']
        cf_start = not_starting * symptoms['not_starting']
        cf_final = calculate_cf(cf_dust, cf_malfunction)
        cf_final = calculate_cf(cf_overheat, cf_final)
        cf_final = calculate_cf(cf_start, cf_final)
        solution = max(cf_malfunction, cf_start, cf_dust, cf_overheat)
        if (solution != 0):
            print("Power Supply solution: ", solution)
            if solution == cf_start or solution == cf_overheat:
                print("You need to change the Power Supply")
            if solution == cf_dust or solution == cf_malfunction:
                print("You need to clean the Power Supply fan or change it")
        self.modify(fact, CF=cf_final, done=1)

    @Rule(salience=3)
    def prints(self):
        rules = []
        p = []
        print('------------- malfunctions --------')
        for factId in list(self.facts):
            if type(self.facts[factId]) is Screen or type(self.facts[factId]) is Sound or type(
                    self.facts[factId]) is HDD or type(self.facts[factId]) is PSU or type(
                self.facts[factId]) is PowerSupply:
                if self.facts[factId]["CF"] != 0:
                    rules.append((self.facts[factId]["name"], self.facts[factId]["CF"]))
                    problems.append((self.facts[factId]["name"], self.facts[factId]["CF"]))
        rules = sorted(rules, key=lambda r: r[1], reverse=True)
        print(rules)
        print('----------------------------------')


########### MAIN ##################

eng = Knowledge()
eng.reset()
eng.run()

# import tkinter as tk
# from tkinter import *
#
# fields = ("Computer not turns on", "psu light on but computer not starts",
#           "hearing loud sound on working", "smell burn", "computer not starting", "hearing cracking sound",
#           "System is not Booting", "hearing click sound", "HDD Heating", "Slow file access", "System crashes",
#           "Screen Stutters", "Screen flickers", "black or colored lines in screen",
#           "No sound", "sound clinking")
#
#
# def find_problems(entries):
#     print("*****************")
#     eng.reset()
#     eng.declare(Info(click_fault=float(entries["Computer not turns on"].get()),
#                      connection_pin=float(entries["psu light on but computer not starts"].get())))
#     eng.declare(Info(fan_dust=float(entries["hearing loud sound on working"].get()),
#                      overheat=float(entries["smell burn"].get()),
#                      not_starting=float(entries["computer not starting"].get()),
#                      fan_malfunction=float(entries["hearing cracking sound"].get())))
#     eng.declare(Info(not_booting=float(entries["System is not Booting"].get()),
#                      clicky=float(entries["hearing click sound"].get()),
#                      heating=float(entries["HDD Heating"].get()),
#                      slow_file_access=float(entries["Slow file access"].get()),
#                      sys_crash=float(entries["System crashes"].get())))
#     eng.declare(
#         Info(stuttering=float(entries["Screen Stutters"].get()), flickering=float(entries["Screen flickers"].get()),
#              led_panel=float(entries["black or colored lines in screen"].get())))
#     eng.declare(Info(no_sound=float(entries["No sound"].get()), clinking=float(entries["sound clinking"].get())))
#     eng.run()
#
#
# def makeform(root, fields):
#     entries = {}
#     for field in fields:
#         row = tk.Frame(root)
#         lab = tk.Label(row, width=35, text=field + ": ", anchor='w')
#         ent = tk.Entry(row)
#         ent.insert(0, 0)
#         row.pack(side=tk.TOP,
#                  fill=tk.X,
#                  padx=5,
#                  pady=5)
#         lab.pack(side=tk.LEFT)
#         ent.pack(side=tk.RIGHT,
#                  expand=tk.YES,
#                  fill=tk.X)
#         entries[field] = ent
#     return entries
#
#
# def changeView():
#     entries = {}
#     root = tk.Tk()
#     for i in range(len(problems)):
#         Label(root, text=problems[i][0], font="15").grid(row=i + 1, sticky=W, padx=30)
#         Label(root, text=problems[i][1], font="15").grid(row=i + 1, sticky=W, padx=300)
#     root.geometry("800x400")
#     root.title("Results")
#
#
# if __name__ == '__main__':
#     root = tk.Tk()
#     ents = makeform(root, fields)
#     b2 = tk.Button(root, text='Find Problems',
#                    command=(lambda e=ents: find_problems(e)))
#     b2.pack(side=tk.LEFT, padx=5, pady=5)
#     b3 = tk.Button(root, text='Quit', command=changeView)
#     b3.pack(side=tk.LEFT, padx=5, pady=5)
#
#     root.mainloop()

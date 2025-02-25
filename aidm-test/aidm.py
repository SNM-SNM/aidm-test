import openai
from openai import OpenAI
import random
import time
import os
from cryptography.fernet import Fernet

import requests


class Character:
    def __init__(self, name = "N/A", classtype = "N/A", race = "N/A", attributes = {}, alignment = "neutral", skills = {}, hp = 100, golds = 100, description = "N/A", story = None):
        self.name = name
        self.classtype = classtype
        self.race = race
        self.attributes = attributes
        self.alignment = alignment
        self.skills = skills
        self.hp = hp
        self.golds = golds
        self.description = description
        self.story = story

    def init_attributes(self):
        """Initialize attributes based on the gamerule of the story"""
        if self.story:
            self.attributes = {attr: 0 for attr in self.story.gameruledict["attributes"]}
        else:
            # 默认属性
            self.attributes = {
                "Strength": 0,
                "Intelligence": 0,
                "Speed": 0,
                "Charisma": 0
            }

    def charaInfo(self):
        """Sum up all character info into a string and return the string"""
        return ("Name: ", self.name, ", Classtype: ", self.classtype, "Race: ", self.race, "Attributes: ", self.attributes, "Alignment: ", self.alignment, "Skills: ", self.skills, "HP: ", self.hp, "Golds: ", self.golds, "Description: ", self.description)
    
    def printCharaInfo(self):
        """Print all character info line by line"""
        print("Name: ", self.name)
        print("Classtype: ", self.classtype)
        print("Race: ", self.race)
        print("Attributes: ")
        for key, value in self.attributes.items():
            print(f"{key}: {value}")
        print("Alignment: ", self.alignment)
        print("HP: ", self.hp)
        print("Golds: ", self.golds)
        print("Skills: ")
        for key, value in self.skills.items():
            print(f"{key}:\n {value}")
        print("\nDescription: ", self.description)
        print("\n")
        
class Story:
    def __init__(self):
        self.history = []
        self.keyevents = []
        self.characters = []
        self.gameruledict = {
            "dice_sides": 6, # The sides of the dice. Default is 6
            "max_attribute_point": 6, # The maximum attribute point (means the character can has attribute point from 1-6). Default is 6
            "attributes": ["Strength", "Intelligence", "Speed", "Charisma"], # The attributes of the character. Default is ["Strength", "Intelligence", "Speed", "Charisma"]
            "success_condition": "total > requirement", # The success condition of the dice roll. Default is "total > requirement"
            "skill_impact": {
                "type": "add_points",
                "format": "Add {value} points to your {attribute} rolls"
            },
            "custom_rules": ["None"] # Custom rules that can be added to the game. Default is ["None"]
        }
        self.gamerule = f"""Let the player to roll dices based on player's {len(self.gameruledict["attributes"])} attribute ({self.gameruledict["attributes"]}). The dice is {self.gameruledict["dice_sides"]} sided, and if character's strength attribute is 4 means the player can roll 4 dices at the same time (4d{self.gameruledict["dice_sides"]}) to have a total. You should decide what kind of attribute should be rolled based on your reasoning.
        Extra custrom rules: "{self.gameruledict["custom_rules"]}". """ # This game rule will be fed into the LLM when there is dice rolling.


    def get_all_story(self):
        return self.history
    
    def get_background(self):
        return self.history[0]
    
    def get_all_key_events(self):
        return self.keyevents
    
    def get_all_chara_info(self):
        list = []
        for chara in self.characters:
            list.append(chara.charaInfo())
        return list
    
    def get_gamerule(self):
        return self.gamerule
    
    def add_event(self, event):
        """Append the event"""
        self.history.append(event)
    
    def get_latest_event(self):
        """Return the latest event"""
        if(self.history[-1].startswith("You do:")):
            return self.history[-2]
        return self.history[-1]
    
    def get_latest_player_action(self, i = -1):
        if(not self.history[i].startswith("You do:")):
            return self.get_latest_player_action(i-1)
        return self.history[i]

    def add_key_event(self, event:str):
        self.keyevents.append(event)

    def add_npc(self, npc:Character):
        self.characters.append(npc)

    def update_gamerule(self, rule_key: str, new_value):
        if rule_key in self.gameruledict:
            self.gameruledict[rule_key] = new_value
        else:
            self.gameruledict["custom_rules"].append({rule_key: new_value})

    def override_gamerule(self, new_rules: dict):
        self.gameruledict.update(new_rules)


def extract_response(response: str, wanted_str: str, start_shift = 2, end_str = "\n", end_shift = 0):
    """Extract the response from the GPT API

    Args:
        response (str): The response from the GPT API
        wanted_str (str): The string that you want to extract
        start_shift (int): The shift of the start of the wanted string, default is 2
        end_str (str): The end of the wanted string, default is "\n"
        end_shift (int): The shift of the end of the wanted string, default is 0
    Return:
        The extracted response
    """
    return response[(response.find(wanted_str) + len(wanted_str) + start_shift): (response.find(end_str, (response.find(wanted_str) + len(wanted_str) + start_shift)) + end_shift)]

def rollDices(character: Character, selectedAttribute: str, requirement: int, story: Story):
    """Let the character roll the dice based on character's attribute. Check if dice total surpass the requirement

    Args:
        character (Character): Character who rolls the dice
        selectedAttribute (str): One of the four attributes of a character
        requirement (int): The total dice number for the event/encounter to be successful
    Return:
        Outcome of the roll
    """
    total = 0
    total_list = []
    dice_sides = story.gameruledict["dice_sides"]  # Get dice_sides from gamerule
    for i in range(character.attributes[selectedAttribute]):
        num = random.randint(1, dice_sides)
        total += num
        total_list.append(num)
    print(f"\nThe dice you have rolled based on your {selectedAttribute} ability: ")
    print(*total_list, sep =', ')
    # Add skills to total
    for skill_key, skill_val in character.skills.items():
        if(selectedAttribute.lower() in skill_val.lower()):
            print(f"""Your skill: "{skill_key}" has contributed to your roll! """)
            value = int(skill_val[skill_val.find("Add") + 4: skill_val.find("point")])
            print(f"{value} points added to your dice rolls")
            total += value
    
    print(f"In total: {total}")
    success_condition = story.gameruledict["success_condition"]
    result = eval(f"{success_condition.replace('requirement', str(requirement))}")
    if(result):
        print("Success!")
        return True
    else:
        print("Fail!")
        return False
    
    
def rollEnemyDices(character: Character, selectedAttribute: str, story: Story):
    """Let the enemy roll the dice based on character's attribute. Returns a int of the total

    Args:
        character (Character): Character who rolls the dice
        selectedAttribute (str): One of the four attributes of a character
    Return:
        Total int of the roll
    """
    total = 0
    total_list = []
    dice_sides = story.gameruledict["dice_sides"]  # Get dice_sides from gamerule
    for i in range(character.attributes[selectedAttribute]):
        num = random.randint(1, dice_sides)
        total += num
        total_list.append(num)
    print(f"\nThe dice your enemy have rolled based on {selectedAttribute} ability: ")
    print(*total_list, sep =', ')
    print(f"Your enemy's dice in total: {total}")
    return total

def command_input(character: Character, story: Story, uinput = ""):
    """Determine whether the input is a command and execute it
    """
    if(uinput==""):
        uinput = input("\nYou do: ")
    if(uinput.startswith("/")):
        # Command of printing player's character info
        if(uinput == "/me"):
            character.printCharaInfo()
            return command_input(character, story)
        # Command of saving the story into a txt file
        elif(uinput.startswith("/save")):
            # Story saving
            file_name = uinput[6 : ]
            with open((file_name + ".txt"), 'w', encoding='utf-8') as file:
                for line in story.get_all_story():
                    file.write(str(line) + '\n')
            # Character saving
            file_name_chara = file_name + "_chara"
            with open((file_name_chara + ".txt"), 'w', encoding='utf-8') as file:
                file.write(f"Name: {character.name}\n")
                file.write(f"Classtype: {character.classtype}\n")
                file.write(f"Race: {character.race}\n")
                file.write(f"Attributes: \n")
                for key, value in character.attributes.items():
                    file.write(f"{key}: {value}\n")
                file.write(f"Alignment: {character.alignment}\n")
                file.write(f"HP: {character.hp}\n")
                file.write(f"Golds: {character.golds}\n")
                file.write(f"Skills: \n")
                for key, value in character.skills.items():
                    file.write(f"{key}:\n {value}\n")
                file.write("\n")
            print(f"Your story has been saved to {file_name}.txt. Your character information has been saved to {file_name_chara}.txt")
            return command_input(character, story)
        elif(uinput.startswith("/read")):
            file_name = uinput[6:].strip()
            success = load_saved_game(character, story, file_name)
            if success:
                print(f"Game loaded from {file_name}! Continuing the story...")
                # Re-print all story for context
                print("\n" + story.get_latest_event())
            return command_input(character, story)
        elif(uinput == ("/events")):
            print(story.get_all_key_events())
            return command_input(character, story)
        elif uinput.startswith("/rule"):
            parts = uinput.split()
            if len(parts) >= 3:
                rule_key = parts[1]
                new_value = " ".join(parts[2:])
                try:
                    # Try to convert the new value to int
                    new_value = int(new_value)
                except:
                    pass
                story.update_gamerule(rule_key, new_value)
                print(f"Rules updated: {rule_key} = {new_value}")
            else:
                print("Invalid rule command. Please use the format: /rule [rule_type] [new_value]")
            return command_input(character, story)
        # Command of listing all commands
        elif(uinput == "/help"):
            print("""
                  Help commands:
                  /me -> Shows the character information of the player
                  /save [file_name] -> Save the story so far into 2 txt file (story and character info).
                  /read [file_name] -> (Might not work perfectly) Load a saved game from 2 txt file (story and character info). 
                  /events -> Shows key events happened
                  /rule [rule_type] [new_value] -> Update the game rule
                  """)
            return command_input(character, story)
        else:
            # Command not found
            print("Command not found")
            return command_input(character, story)

    return uinput

def load_saved_game(player: Character, story: Story, file_name: str):
    """Load saved game from files"""
    try:
        # Load story
        story_file = file_name + ".txt"
        with open(story_file, 'r', encoding='utf-8') as file:
            story.history = [line.strip() for line in file.readlines() if line.strip()]
        
        # Load character
        chara_file = file_name + "_chara.txt"
        with open(chara_file, 'r', encoding='utf-8') as file:
            chara_data = file.read()
            
            # Extract character properties
            player.name = extract_response(chara_data, "Name")
            player.classtype = extract_response(chara_data, "Classtype")
            player.race = extract_response(chara_data, "Race")
            player.alignment = extract_response(chara_data, "Alignment")
            player.hp = int(extract_response(chara_data, "HP"))
            player.golds = int(extract_response(chara_data, "Golds"))
            # Debug prints (optional)
            # hp_str = extract_response(chara_data, "HP:")
            # print("Debug: Extracted HP:", hp_str)
            # player.hp = int(hp_str) if hp_str else 0
            
            # golds_str = extract_response(chara_data, "Golds:")
            # print("Debug: Extracted Golds:", golds_str)
            # player.golds = int(golds_str) if golds_str else 0
            
            # Extract attributes
            player.attributes = {
                "Strength": int(extract_response(chara_data, "Strength")),
                "Intelligence": int(extract_response(chara_data, "Intelligence")),
                "Speed": int(extract_response(chara_data, "Speed")),
                "Charisma": int(extract_response(chara_data, "Charisma"))
            }
            
            # Extract skills
            skills_section = chara_data.split("Skills:")[1]
            skills = {}
            current_skill = None
            for line in skills_section.split('\n'):
                line = line.strip()
                if line.endswith(':'):
                    current_skill = line[:-1]
                    skills[current_skill] = ""
                elif current_skill:
                    skills[current_skill] += line + '\n'
            player.skills = {k: v.strip() for k, v in skills.items() if k}
            
        return True
    except FileNotFoundError:
        print(f"Error: Save files '{file_name}' not found!")
        return False
    except Exception as e:
        print(f"Error loading game: {str(e)}")
        return False

def generateKeyEvent(response: str):
    keyevent = gpt([{'role': 'user','content':
                                   f"""You're a Dungeon Master of a heroic saga. This is your latest generation: "{response}". Based on this, summarize this event in 1 or 2 sentences. You should only return and summarize it in 1 or 2 sentences.
                                     Write in second person present tense (you are), avoiding letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=False)
    return keyevent
    

def startDM(player: Character, story: Story):
    player.story = story  # 添加故事引用
    player.init_attributes()
    response = gpt([{'role': 'user','content':
                                   f"""You're a Dungeon Master of a heroic saga. Create a background for this Dungeon and Dragon game. Your background should describe the setting where the adventure takes place, including its geography, cultures, and history.
                                   At the end, randomly generate 4 characters to let the player choose their characters. The characters you generated should have reasonable properties and attributes, and the characters generated should be in this form:
                                   "
                                   Character 1
                                   Classtype: Fighter, Wizard, Rogue, etc.
                                   Race: Human, Elf, Dwarf, Halfling, etc.
                                   Attributes:""" +
                                    "\n".join([f"  {attr} = A number from 1 - {story.gameruledict['max_attribute_point']}" for attr in story.gameruledict['attributes']]) +
                                   """Alignment: Lawful, Neutral, Chaotic, Good, Evil, etc.
                                   Description: A short description for this character
                                   "
                                   Make sure you use the exact words examples provided above (such as when writing Classtype, do not change the word and write it to Class Type). Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    # print(response)

    # Record the generated story background
    background = response[ : (response.find("Character"))]
    story.add_event(background)
    chara = response[(response.find("Character")) : ]
    story.add_event(chara)

    # Let player choose character
    print("\nInput a number from 1 to 4 to choose your character. Or input 0 to create a custom character.")
    user_input = input("Your choice is: ")
    story.add_event("You do: " + user_input)
    if(int(user_input)==0):
        # Custom character creation
        print("\nYou have chosen to create a custom character.")
        print("Please provide any detail for your character:")
        custom_description = input("Description: ")
        # Generate a character based on custom properties
        
        response = gpt([{'role': 'user', 'content': 
                       f"""
                        Create a Dungeons and Dragons character based on the following properties provided by the player: "{custom_description}". The form of your generation should be based on the following:
                        "
                        Classtype: custom_classtype
                        Race: custom_race
                        Attributes:"""+
                          "\n".join([f"  {attr} = A number from 1 - {story.gameruledict["max_attribute_point"]}" for attr in story.gameruledict["attributes"]]) +
                        """Alignment: Lawful, Neutral, Chaotic, Good, Evil, etc.
                        Description: A short description for this character
                        "
                        You should not continue or write any story after generating character information. All you need to do is to generate a character based on the properties provided by the player.
                        Make sure you use the exact words examples provided above (such as when writing Classtype, do not change the word and write it to Class Type). Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                        """}], printChunk=True)
        choice = response[:]
    elif(int(user_input)<4 and int(user_input)>0):
        choice = response[(response.find(f"Character {user_input}")) : response.find(f"Character {str(int(user_input)+1)}")]
    elif(int(user_input)==4):
        choice = response[(response.find(f"Character {user_input}")) : ]
    else:
        print("Invalid input. Please input a number from 1 to 4. Start over.")
        return startDM(player, story)

    # Extract properties of player's character and save them into Character class
    player.classtype = extract_response(choice, "Classtype")
    player.race = extract_response(choice, "Race")
    # player.attributes = {
    #     "Strength": int(extract_response(choice, "Strength")),
    #     "Intelligence": int(extract_response(choice, "Intelligence")),
    #     "Speed": int(extract_response(choice, "Speed")),
    #     "Charisma": int(extract_response(choice, "Charisma"))
    # }
    for attr in story.gameruledict["attributes"]:
        player.attributes[attr] = int(extract_response(choice, attr))
    player.alignment = extract_response(choice, "Alignment")
    player.description = extract_response(choice, "Description")
    story.add_npc(player)
    print("You have created your character. There is your character properties: ")
    player.printCharaInfo()
    # story.add_event(player.charaInfo())
    input("Confirm your information. Press enter to start the story: ")
    
def startStory(player: Character, story: Story):
    """Start the story with the player's character and the background information"""
    response = gpt([{'role': 'user','content':
                                   f"""
                                   You may now start creating story (D&D) as a Dungeon Master based on the background information: "{story.get_background()}", and player's character information: "{player.charaInfo()}". 
                                   Your generation should be rich, diverse, creative, and reasonable based on the background information provided. At the end of your generation, ask what the player would do next (you don't need to generate options for this). 
                                   Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    story.add_event(response)
    story.add_key_event(generateKeyEvent(response))
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)

def loadStory(player: Character, story: Story):
    """Load the story from the saved files"""
    response = response = gpt([{'role': 'user','content':
                                   f"""
                                   You may now start continue the story (D&D) as a Dungeon Master based on the background information: "{story.history[0:5]}", and player's character information: "{player.charaInfo()}", and the latest story:"{story.history[-5:]}". 
                                   Your generation should be rich, diverse, creative, and reasonable based on the background information provided. Also your generation should be consistant with the latest story provided. At the end of your generation, ask what the player would do next (you don't need to generate options for this). 
                                   Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    story.add_event(response)
    
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)

def checkEvent(player: Character, story: Story):
    """Check the previous event and decide what should be the following event type based on the previous event
    Return: One of the following event types: Casual Event, Trade, Encounter, Battle, or None (just continue without any type).
    """
    response = gpt([{'role': 'user','content':
                                   f"""
                                   You, as the Dungeon Master, should decide what event type would happen next based on the latest story: "{story.get_latest_event()}", and the player's input: "{story.get_latest_player_action()}". 
                                   The event type should only be one of the 5 following: Casual Event, Trade, Encounter, Battle, or None. 
                                   For Casual Event, the player might meet NPC to get some help/free reward.
                                   For Trade, the player might meet NPC to trade.
                                   For Encounter, the player might meed hostile NPC.
                                   For Battle, if the player initiatively attacks.
                                   You can generate "None" type event if and only if you think based on the latest story and the player's input, that the event type should be happening next doesn't align to 4 other types of event (e.g. the story can just continue without any event occurrence. Or the player's input does not quite make sense). All you need to do is just generate the event type, do not generate any content of the future event.
                                   Let the event be rich, diverse, and creative. Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=False)
    # print(response)
    if("Casual Event" in response):
        return "Casual Event"
    elif("Trade" in response):
        return "Trade"
    elif("Encounter" in response):
        return "Encounter"
    elif("Battle" in response):
        return "Battle"
    elif("None" in response):
        return "None"

        
def encounter(player: Character, story: Story):
    response = gpt([{'role': 'user','content':
                                   f"""
                                   Continue creating story (D&D) based on the character: "{player.charaInfo()}", the background: "{story.get_background()}", the key events before: "{story.get_all_key_events()}", and the latest story: "{story.get_latest_event()}". 
                                   At the end of your generation, create an encounter for the player (you should write out the word "Encounter" in a new line so the player knows). Potentially, this encounter could lead to a battle.
                                   Let the encounter be rich, diverse, and creative. Here are some types of creature information you may use: beasts (Wolves, bears, giant spiders, etc), humanoids (Goblins, orcs, kobolds, gnolls, lizardfolk, bandits, etc), undead(Skeletons, zombies, wights, ghouls, vampires, liches, etc), aberrations, dragons, fiends, celestials, elementals, giants, golems, fey (pixies, dryads, hags), monstrosities, oozes, plants (treants), swarms, shapechangers, legendary creatures, or just other humans.
                                   You should not provide any options for the encounter. You should not roll and generate the outcome of this event/encounter by yourself. All you need is to generate an encounter and let the player decide what they do.
                                   Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    # Record the generated story background
    story.add_event(response)
    story.add_key_event(generateKeyEvent(response))
    # Input the encounter roll option
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)
    input_response = gpt([{'role': 'user','content':
                                   f"""
                                   Based on the key events before: "{story.get_all_key_events()}" and the latest story: " {story.get_latest_event()}", the player now choose to deal with the encounter by doing: "{user_input}". 
                                   Create an option that if the player choose to do so. Game rule:"{story.get_gamerule()}".
                                   The example of an option is like (assuming the player inputs that he/she wants to scare off the wolves. So the encounter tests on character's Strength (assuming the character has a value of 4)):
                                   "
                                   Option: Intimidate the Wolves (Strength)
                                    You try to scare off the wolves, let the wolves back down and allow the party to pass.
                                    Roll: To successfully intimidate the wolves through physical force, your dice total should be > 18.
                                   "
                                   You must let the attribute to be in brackets(). You must use ">" sign and do not use * signs around the number. You should not roll and generate the outcome of this event/encounter by yourself. All you need is to generate an option with a passing dice total.
                                   Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    # Feed the option to a local method
    story.add_event(input_response)
    story.add_key_event(generateKeyEvent(response))
    choice = input_response
    optionName = choice[(choice.find("Option")) : choice.find("\n")]
    selectedAttribute = choice[(choice.find("(") + 1) : choice.find(")")]
    requirement = int(choice[(choice.find(">") + 2) : choice.find(".", (choice.find(">") + 2))])
    rollOutcome = rollDices(player, selectedAttribute, requirement, story)
    # If roll total > requirement, no need for battle. Get reward.
    if(rollOutcome==True):
        response = gpt([{'role': 'user','content':
                                   f"""
                                   The player has rolled a number greater than the requirement and passed the test. This means the outcome of {optionName} is successful. Continue the story with this successful outcome. At the end, give the player the reward for passing the encounter.
                                   The reward type can be one of these: adding golds, HP (health points), and giving the player a new skill. The probabilities of each type are: 60%, 25%, 15%.
                                   You should write and indicate the word "Reward" so that the player can see. An exmaple of golds reward is like the following (You must use the word "Golds"):
                                   "
                                    Reward: Golds +50

                                   "  
                                   An example of HP reward (you should always capitalize HP):
                                   "
                                    Reward: HP +15

                                   "
                                   An example of new skill reward (Note that you should design the skill with proper reasoning. You have to include the words: "New skill", "Skill Description", and "Effect". After the name of the skill, there should be a notation (one of the attributes) in the bracket indicating this skill's property (e.g. New skill: xxx (Strength)). 
                                   The skill type will be "{story.gameruledict["skill_impact"]["type"]}". For the effect, you must have a description of "{story.gameruledict["skill_impact"]["format"]}", where "value" is a proper reasonable value and "attribute" is one of the {len(story.gameruledict["attributes"])} character attributes ({story.gameruledict["attributes"]}). These are the only {len(story.gameruledict["attributes"])} attributes that you must use, do not add any other new attributes (Such as, do not make a skill and say "Add 5 points to your HP rolls")):
                                   "
                                    Reward: New skill: Pursue and Empower (Strength)
                                    Skill Description: You are learning the skill Pursue and Empower, a dynamic ability that enhances your capacity to chase down enemies and motivate your allies during combat. This skill emphasizes both speed and teamwork, allowing you to close the gap on foes and inspire your companions to give their best. 
                                    Effect: Add 6 points to your strength rolls.
                                   "
                                   Make an empty new line at the end of your generation.
                                   Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
        # Record the reward
        story.add_event(response)
        story.add_key_event(generateKeyEvent(response))
        if("Golds" in response):
            player.golds += int(response[(response.find("Golds") + 7) : response.find("\n", (response.find("Golds") + 7))])
        elif("HP" in response):
            player.hp += int(response[(response.find("HP") + 4) : response.find("\n", (response.find("HP") + 4))])
        elif("New skill" in response):
            skillName = response[(response.find("New skill:")+ 11)  : response.find("\n", (response.find("New skill:")+ 11))]
            skillDescription = response[(response.find("Description")) : response.find("Effect")]
            skillEffect = response[(response.find("Effect")) : response.find("rolls") + 6]
            player.skills.update({skillName: (skillDescription+skillEffect)})
            print("Your skills are updated:")
            player.printCharaInfo()

        print("\nYou have gone through the encounter successfully. What would you like to do next?")
        user_input = command_input(player, story)
        story.add_event("You do: " + user_input)
    # If encounter roll fails, the encounter becomes a battle.
    else:
        battle(player, story)
    print("\n------------------------------")

def battle(player: Character, story: Story):
    response = gpt([{'role': 'user','content':
                                   f"""
                                   The player has rolled a number less than the requirement and failed the test. You should now continue the  previous encounter story: "{story.get_latest_event()}". The key events before are: "{story.get_all_key_events()}". Now, this encounter leads to an actual battle (you should write out the word "Battle" in a new line so the player knows). 
                                   Use the previous information. Generate character information for the enemy in the following example form (do not generate multiple enemies):
                                   "
                                   Enemy name: (Name that you may generate. If the enemy is just a or some creatures just write the creature or race names) 
                                   Classtype: (A class type that's aligned to the race below)
                                   Race: beasts (Wolves, bears, giant spiders, etc), humanoids (Goblins, orcs, kobolds, gnolls, lizardfolk, bandits, etc), undead(Skeletons, zombies, wights, ghouls, vampires, liches, etc), aberrations, dragons, fiends, celestials, elementals, giants, golems, fey (pixies, dryads, hags), monstrosities, oozes, plants (treants), swarms, shapechangers, legendary creatures, or just humans.
                                   Attributes:"""+
                                    "\n".join([f"""  {attr} = A number from 1 - {story.gameruledict['max_attribute_point']}""" for attr in story.gameruledict["attributes"]]) +
                                    """Alignment: Lawful, Neutral, Chaotic, Good, Evil, etc.
                                   HP: A number from 20 to 200
                                   Description: A short description for this enemy
                                   "
                                   Do not generate any other signs or words other than the ones provided above.
                                   After genearting enemy information, write a short description of the battle between the player (player's info: "{player.charaInfo()}") and the enemey. At the end, ask what player would do next.
                                   Make sure you use the exact words examples provided above (such as when writing Classtype, do not change the word and write it to Class Type). Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    
    story.add_event(response)
    # Record the enemy
    enemy = Character(
        name = extract_response(response, "Enemy name"),
        classtype = extract_response(response, "Classtype"),
        race= extract_response(response, "Race"),
        alignment= extract_response(response, "Alignment"),
        hp = int(extract_response(response, "HP")),
        description = extract_response(response, "Description")
    )
    for attr in story.gameruledict["attributes"]:
        enemy.attributes[attr] = int(extract_response(response, attr))
    story.add_npc(enemy)
    # Keep battling until the enemy's HP <= 0
    battling = True
    while(battling):
        # Input what player would do
        user_input = command_input(player, story)
        story.add_event("You do: " + user_input)
        input_response = gpt([{'role': 'user','content':
                                       f"""
                                       Based on the key events before: "{story.get_all_key_events()}", the latest battle:"{story.get_latest_event()}" and enemy info:"{enemy.charaInfo()}": , the player (info:"{player.charaInfo()}") now choose to deal with the battle by doing: "{user_input}". 
                                       Create an option that if the player choose to do so. Game rule:"{story.get_gamerule()}".
                                       The example of an option is like (assuming the player inputs that he/she wants to attack wolves using strength. So the encounter tests on character's Strength (assuming the character has a value of 4)):
                                       "
                                       Option: Draws your longsword and charges at the wolves (Strength)
                                        Description: You lets out a battle cry and steps forward, raising your longsword high above your head. The wolves darts to the side, its sharp eyes tracking your every movement. You adjusts your stance and swings the blade in a powerful arc.
                                        Roll: To successfully attack the wolves through physical force, your dice total should be greater than the roll of the wolves.
                                       "
                                       You must state the option in the form above and include the words "Option", "Description", and "Roll". You must let the attribute (one of Strength, Intelligence, Speed, Charisma) to be in brackets() at the Option line. Keep the option line short and let description of the option to have more details. You should not roll and generate the outcome of this event/encounter by yourself. All you need is to generate an option with a description of the attack.
                                       Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                       """},], printChunk=True)

        story.add_event(input_response)
        story.add_key_event(generateKeyEvent(input_response))
        # Feed the option to a local method
        choice = input_response
        optionName = choice[(choice.find("Option")) : choice.find("\n")]
        selectedAttribute = choice[(choice.find("(") + 1) : choice.find(")")]
        # Compare the roll between the player and the enemy
        rollOutcome = rollDices(player, selectedAttribute, rollEnemyDices(enemy, selectedAttribute, story), story)
        # When player wins the roll
        if(rollOutcome==True):
            response = gpt([{'role': 'user','content':
                                       f"""
                                       The player has rolled a number greater than the enemy's and passed the previous battle: "{story.get_latest_event()}". This means the outcome of {optionName} is successful. Continue the story with this successful outcome. The infomation of the enemy is {enemy.charaInfo}. 
                                       If the player's option is to attack, you should give the enemy certain amount of damage. State the outcome of this attack and write the damage given to the enemy in a newline so that the player can see. You should write it in the following form:
                                       "
                                        Damage: (you should decide the number of damage. If the player's attack is severe, you can give a higher number of damage (50+). If the player's attack is weak, you can give a lower number of damage(around 10 to 30))
                                        Description: (How the player cause the damage)
                                       "
                                       You must keep it in the form above and you must use the word "Damage" (Do not add any sign around it). You don't need to calculate the damage to enemy's HP. Just give a number of damage and describe how the player cause the damage.
                                       If the player's option is to run away or escape, you should write the description of the escape and ask the player what they would do next. You must write "You've escaped" at a new line at the end of your generated texts.
                                       If the player's option is to heal,  you should write the description of the heal and you must write "You've successfully healed" and provide a number of HP healed at the end of your generated texts. 
                                       Example of healing: "You've successfully healed. HP +20". You must write "HP" and "+" and keep a space between them.
                                       Make an empty new line at the end of your generation.
                                       Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                       """},], printChunk=True)
            # Record the damage
            story.add_event(response)
            story.add_key_event(generateKeyEvent(response))
            if("You've escaped" in response):
                battling = False
                user_input = command_input(player, story)
                story.add_event("You do: " + user_input)
                return
            if("HP +" in response):
                player.hp += int(extract_response(response, "HP"))
            if("Damage:" in response):
                damage = int(extract_response(response, "Damage"))
                enemy.hp -= damage
            # If enemy's HP <= 0: Player wins the Battle
            if(enemy.hp <= 0):
                battling = False
                response = gpt([{'role': 'user','content':
                                       f"""
                                       For previous key events:"{story.get_all_key_events()}" and the previous battle: "{story.get_latest_event()}", the enemy has been defeated. Continue the story with this successful outcome. The infomation of the enemy is {enemy.charaInfo()}. At the end, give the player the reward for winning the battle.
                                       The reward type can be one of these: adding golds, HP (health points), and giving the player a new skill. The probabilities of each type are: 30%, 10%, 60%.
                                       You should write and indicate the word "Reward" so that the player can see. An exmaple of golds reward is like the following:
                                       "
                                        Reward: Golds +200

                                       "  
                                       An example of HP reward (you should always capitalize HP):
                                       "
                                        Reward: HP +40

                                       "
                                       An example of new skill reward (Note that you should design the skill with proper reasoning. You have to include the words: "New skill", "Skill Description", and "Effect". After the name of the skill, there should be a notation (one of the attributes) in the bracket indicating this skill's property (e.g. New skill: xxx (Strength)). 
                                        The skill type will be "{story.gameruledict["skill_impact"]["type"]}". For the effect, you must have a description of "{story.gameruledict["skill_impact"]["format"]}", where "value" is a proper reasonable value and "attribute" is one of the {len(story.gameruledict["attributes"])} character attributes ({story.gameruledict["attributes"]}). These are the only {len(story.gameruledict["attributes"])} attributes that you must use, do not add any other new attributes (Such as, do not make a skill and say "Add 5 points to your HP rolls")):
                                        "
                                         Reward: New skill: Pursue and Empower (Strength)
                                         Skill Description: You are learning the skill Pursue and Empower, a dynamic ability that enhances your capacity to chase down enemies and motivate your allies during combat. This skill emphasizes both speed and teamwork, allowing you to close the gap on foes and inspire your companions to give their best. 
                                         Effect: Add 6 points to your strength rolls.
                                        "
                                       Make an empty new line at the end of your generation.
                                       Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                       """},], printChunk=True)
                story.add_event(response)
                story.add_key_event(generateKeyEvent(response))
                response = response[response.find("Reward") : ]
                if("Golds" in response):
                    player.golds += int(extract_response(response, "Golds"))
                if("HP" in response):
                    player.hp += int(extract_response(response, "HP"))
                if("New skill" in response):
                    skillName = extract_response(response, "New skill")
                    # skillDescription = response[(response.find("Description")) : response.find("Effect")]
                    skillDescription = extract_response(response, "Description", end_str="Effect")
                    # skillEffect = response[(response.find("Effect")) : response.find("rolls") + 6]
                    skillEffect = extract_response(response, "Effect", end_str="rolls", end_shift=6)
                    player.skills.update({skillName: (skillDescription+skillEffect)})
                    print("Your skills are updated:")
                    player.printCharaInfo()
                print("\nYou have won the battle. What would you like to do next?")
                user_input = command_input(player, story)
                story.add_event("You do: " + user_input)
            # If enemy's HP still > 0. Battle continues
            else:
                print(f"\nThe enemy's HP: {enemy.hp}. Battle continues")
        # When player loses the roll
        else:
            response = gpt([{'role': 'user','content':
                                       f"""
                                       The player has rolled a number less than the enemy's and failed the previous battle: "{story.get_latest_event()}". This means the outcome of {optionName} is not successful. Continue the story with this a failing outcome. The infomation of the enemy is {enemy.charaInfo()}. You should give the player certain amount of damage.
                                       State the outcome of this attack and write the damage given to the player in a newline so that the player can see. You should write it in the following form:
                                       "
                                        Damage: (you should decide the number of damage) 
                                        Description: (How the player cause the damage)
                                       "
                                       You must keep it in the form above and use the word "Damage" (Do not add any sign around it). You don't need to calculate the damage to player's HP. Just give a number of damage.
                                       Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                       """},], printChunk=True)
            # Record the damage
            story.add_event(response)
            story.add_key_event(generateKeyEvent(response))
            if("Damage:" in response):
                damage = int(extract_response(response, "Damage"))
                player.hp -= damage
            # If player's HP <= 0: Game over
            if(player.hp <= 0):
                print("\nYour HP is 0. Game over")
                exit()
            # If player's HP still > 0, the battle continues
            else:
                print(f"\nYour HP: {player.hp}. The battle continues")

def event(player: Character, story: Story):
    response = gpt([{'role': 'user','content':
                                   f"""
                                   You can now continue creating story (D&D) as the Dungeon Master. Your generation should align to the previous key events: "{story.get_all_key_events()}," previous story: "{story.get_latest_event()}", the background world information: "{story.get_background()}", and the player's information: "{player.charaInfo()}".
                                   At the end of your generation, create a casual event between the player and the NPC that allows NPCs to offer the player some help. You should indicate the word "Casual Event" so that the player knows.
                                   There are some types of NPCs you may consider: The Quest Giver, the Merchant, the Healer, the Informant, the Trainer, the Patron, the Keeper of Secrets, the Protector, the Wise Elder, etc.
                                   You should descibe the event. At the end, ask what the player wants to do. (You don't need to generate options for the player to choose. Just state the event and let the player input the action)
                                   Let the event and NPC be rich, diverse, and creative. Here are some examples:
                                   An example of the Quest Giver: desperate villager pleading for help against a marauding monster. May reward players with gold.
                                   An example of the Healer: a wandering druid offering natural remedies. May reward players with HP.
                                   An example of the Wise Elder: a retired hero who once faced similar challenges. May reward players with a new skill.
                                   
                                   Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    story.add_event(response)
    story.add_key_event(generateKeyEvent(response))
    # Input what player would do
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)
    input_response = gpt([{'role': 'user','content':
                                       f"""
                                       Based on the latest event: " {story.get_latest_event()}", the player now choose to deal with the event and NPC by doing: "{user_input}". 
                                       Create the outcome that if the player chooses to do so, and you may generate a reward or a penalty that player would gain or lose from the event. There are 3 types of reward (Golds, HP, New skill) and 2 types of penalty (Golds, HP) for the player. You should decide whether it should be a reward or a penalty, and what kind of reward or penalty it should be based on your reasoning. 
                                       You should write and indicate the word "Reward" or "Penalty" so that the player can see. 
                                       The example of a Golds reward is like (assuming the player inputs that he/she helps the village and kills the orge):
                                       "
                                        (...... State how villagers show gratitudes and thank the player)
                                        Reward: Golds +50
                                        Description:()
                                       "
                                       An example of HP reward (you should always capitalize HP):
                                       "
                                        (...... State how villagers take care of the player after killing the orge)
                                        Reward: HP +30
                                        Description: ()
                                       "
                                       An example of new skill reward (Note that you should design the skill with proper reasoning. You have to include the words: "New skill", "Skill Description", and "Effect". After the name of the skill, there should be a notation (one of the attributes) in the bracket indicating this skill's property (e.g. New skill: xxx (Strength)). 
                                       The skill type will be "{story.gameruledict["skill_impact"]["type"]}". For the effect, you must have a description of "{story.gameruledict["skill_impact"]["format"]}", where "value" is a proper reasonable value and "attribute" is one of the {len(story.gameruledict["attributes"])} character attributes ({story.gameruledict["attributes"]}). These are the only {len(story.gameruledict["attributes"])} attributes that you must use, do not add any other new attributes (Such as, do not make a skill and say "Add 5 points to your HP rolls")):
                                        "
                                         Reward: New skill: Pursue and Empower (Strength)
                                         Skill Description: You are learning the skill Pursue and Empower, a dynamic ability that enhances your capacity to chase down enemies and motivate your allies during combat. This skill emphasizes both speed and teamwork, allowing you to close the gap on foes and inspire your companions to give their best. 
                                         Effect: Add 6 points to your strength rolls.
                                        "
                                       An example of a Golds penalty is like (assuming the player inputs that he/she refuses to help):
                                       "
                                       (...... State that villagers are upset. A theif steals the player's Golds when he/she doesn't notice)
                                       Penalty: Golds -20
                                       Description:()
                                       "
                                       An example of a HP penalty is like (assuming the player inputs that he/she insults the NPC):
                                       "
                                       (...... State how the player gets punished)
                                       Penalty: HP -20
                                       Description:()
                                       "
                                       You may have reward and penalty at the same time. For example, the player kills the orge and gets Golds reward, but the player also gets HP penalty because the player gets injured.
                                       "
                                       Reward: Golds +50
                                       Penalty: HP -20
                                       Description:()
                                       "
                                       You should always keep a space between the attribute (HP or Golds) and the sign (+ or -).
                                       Let the event and NPC be rich, diverse, and creative. Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                       """},], printChunk=True)
    story.add_event(input_response)
    story.add_key_event(generateKeyEvent(response))
    if("Golds" in input_response):
        if("Golds +" in input_response):
            player.golds += int(extract_response(input_response, "Golds"))
        if("Golds -" in input_response):
            player.golds -= int(extract_response(input_response, "Golds"))
    if("HP" in input_response):
        if("HP +" in input_response):
            player.hp += int(extract_response(input_response, "HP"))
        if("HP -" in input_response):
            player.hp -= int(extract_response(input_response, "HP"))
    if("New skill" in input_response):
        skillName = extract_response(input_response, "New skill")
        skillDescription = extract_response(input_response, "Skill Description", end_str="Effect")
        skillEffect = extract_response(input_response, "Effect", end_str="rolls", end_shift=6)
        player.skills.update({skillName: (skillDescription+skillEffect)})
        print("\nYour skills are updated:")
        player.printCharaInfo()
    print("You have gone through the casual event. What would you like to do next?")
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)

def trade(player: Character, story: Story):
    response = gpt([{'role': 'user','content':
                                   f"""
                                   You can now continue creating story (D&D) as a Dungeon Master with the character information: "{player.charaInfo()}". The story background: "{story.get_background()}". Previous key events:"{story.get_all_key_events()}". Previous story: "{story.get_latest_event()}".
                                   At the end of your generation, create an trade event. The trade event allows the player to give up HP or Golds, and gain Golds, HP, or learning a skill. The only 2 things that the player can give up for the trade are HP and Golds. The only 3 things that the player can gain from the trade are HP, Golds, and a new skill. You may provide multiple options for the player to choose.
                                   An example of a trade event is like:
                                   "
                                    Trade: You meet a merchant who offers to sell you a rare potion. The potion costs 25 Golds. If you buy it, you can gain 20 HP. Do you want to buy it? 
                                    You lose: Golds -25
                                    You gain: HP +20
                                   "
                                   Or another example of new skill trading (Note that you should design the skill with proper reasoning. You have to include the words: "New skill", "Skill Description", and "Effect". After the name of the skill, there should be a notation (one of the attributes) in the bracket indicating this skill's property (e.g. New skill: xxx (Strength)). 
                                   The skill type will be "{story.gameruledict["skill_impact"]["type"]}". For the effect, you must have a description of "{story.gameruledict["skill_impact"]["format"]}", where "value" is a proper reasonable value and "attribute" is one of the {len(story.gameruledict["attributes"])} character attributes ({story.gameruledict["attributes"]}). These are the only {len(story.gameruledict["attributes"])} attributes that you must use, do not add any other new attributes (Such as, do not make a skill and say "Add 5 points to your HP rolls")):

                                   "
                                    Trade: You encounter a mysterious figure who offers to teach you the skill of Master Blacksmithing. This skill costs 100 Golds. Do you want to learn it?
                                    You lose: Golds -100
                                    You gain: New skill: Master Blacksmithing (Strength)
                                    Description: You are learning the skill of Master Blacksmithing, a highly sought-after talent that allows you to forge weapons, armor, and other metal items with unparalleled craftsmanship. This skill not only enhances your ability to create, but it also enables you to repair and enchant existing gear.
                                    Effect: Add 10 points to your strength rolls.
                                   "
                                   
                                   You should indicate the word "Trade" so that the player can see. If the player is gaining a new skill, you must have a effect description of "Add x points to your xxx rolls", where x is a proper reasonable value and xxx is one of the {len(story.gameruledict["attributes"])} character attributes ({story.gameruledict["attributes"]}). These are the only {len(story.gameruledict["attributes"])} attributes that you must use, do not add any other new attributes (Such as, do not make a skill and say "Add 5 points to your HP rolls")). You must use the exact words examples provided above (such as you must use "You lose" and "You gain", and when writing Effect, keep it as Effect and do not add signs around it). Do not generate any other options after stating the trade information above.
                                   Let the event be rich, diverse, and creative. Let the skills provided align to the character's information (classtype) provided above. Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    # Record the generated story background
    story.add_event(response)
    story.add_key_event(generateKeyEvent(response))
    # Choose the first encounter roll option
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)
    response = gpt([{'role': 'user','content':
                                   f"""
                                   Based on the latest trade event: " {story.get_latest_event()}", the player now choose to trade with the NPC by doing (or choosing): "{user_input}".
                                   If the player gives up the trade, you should generate the story outcome based on that.
                                   If the player demands a trading that does not align to previous event or the player's input is not reasonable (for example, the merchant sells the potion for 25 Golds and the player wants to buy it for 5 Golds), the trade would fail and you should generate the story outcome based on that.
                                   If the player chooses to trade and the trade is valid based on previous trade event, you should write the trade in the following form:
                                   "
                                    You lose: (Golds -50) or (HP -20)
                                    You gain: (Golds +50) or (HP +20) or (New skill: Master Blacksmithing)
                                   "
                                   You should always keep a space between the attribute (HP or Golds) and the sign (+ or -)
                                   If the player is trading for a new skill, you should generate the new skill in the following example form (assuming the player inputs that he/she wants to learn the skill of Master Blacksmithing by spending 100 Golds)
                                   An example of new skill (Note that you should design the skill with proper reasoning. You have to include the words: "New skill", "Skill Description", and "Effect". After the name of the skill, there should be a notation (one of the attributes) in the bracket indicating this skill's property (e.g. New skill: xxx (Strength)). 
                                    The skill type will be "{story.gameruledict["skill_impact"]["type"]}". For the effect, you must have a description of "{story.gameruledict["skill_impact"]["format"]}", where "value" is a proper reasonable value and "attribute" is one of the {len(story.gameruledict["attributes"])} character attributes ({story.gameruledict["attributes"]}). These are the only {len(story.gameruledict["attributes"])} attributes that you must use, do not add any other new attributes (Such as, do not make a skill and say "Add 5 points to your HP rolls"))
                                   "
                                    You lose: (Golds -100)
                                    You gain: New skill: Master Blacksmithing
                                    Description: You are learning the skill of Master Blacksmithing, a highly sought-after talent that allows you to forge weapons, armor, and other metal items with unparalleled craftsmanship. This skill not only enhances your ability to create, but it also enables you to repair and enchant existing gear.
                                    Effect: Add 10 points to your strength rolls.
                                   "
                                   You must use the exact words examples provided above (such as when writing Effect, keep it as Effect and do not add signs around it). 
                                   Let the event and the skills that can be traded to be rich, diverse, and creative. Let the skills provided align to the character's information (classtype) provided above. Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    story.add_event(response)
    story.add_key_event(generateKeyEvent(response))
    if("You lose" in response):
        choice = response[(response.find("You lose")) : ]
        if("Golds -" in choice):
            player.golds -= int(extract_response(choice, "Golds"))
        if("HP -" in choice):
            player.hp -= int(extract_response(choice, "HP"))
    if("You gain" in response):
        choice = response[(response.find("You gain")) : ]
        if("Golds +" in choice):
            player.golds += int(extract_response(choice, "Golds"))
        if("HP +" in choice):
            player.hp += int(extract_response(choice, "HP"))
        if("New skill" in choice):
            skillName = extract_response(choice, "New skill")
            skillDescription = extract_response(choice, "Description", end_str="Effect")
            skillEffect = extract_response(choice, "Effect", end_str="rolls", end_shift=6)
            player.skills.update({skillName: (skillDescription+skillEffect)})
            print("Your skills are updated:")
            player.printCharaInfo()

    print("\nYou have gone through the trade event. What would you like to do next?")
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)

def continueStory(player: Character, story: Story):
    response = gpt([{'role': 'user','content':
                                   f"""
                                   Continue creating story (D&D) based on the character: "{player.charaInfo()}", the background: "{story.get_background()}", the previoius key events:"{story.get_all_key_events()}", the latest story: "{story.get_latest_event()}, and the player's latest action:"{story.get_latest_player_action()}" ". 
                                   Your generation should be rich, diverse, creative, and reasonable based on the background information provided. Also your generation should be consistant with the latest story and player's action provided. 
                                   At the end of your generation, ask what the player would do next (you don't need to generate options for this).
                                   Write in second person present tense (you are), avoiding summary and letting scenes play out in real time, without skipping. Allow all characters to take the lead and let bad things happen to good people.
                                   """},], printChunk=True)
    story.add_event(response)
    story.add_key_event(generateKeyEvent(response))
    user_input = command_input(player, story)
    story.add_event("You do: " + user_input)
    
# load_dotenv()
# # Retrieve encryption key from .env
# encryption_key = os.getenv("ENCRYPTION_KEY")
# if encryption_key is None:
#     raise ValueError("Missing encryption key in .env file!")
with open('secret.key', 'rb') as key_file:
    key = key_file.read()

f = Fernet(key)

url = "https://getapikey-1099304568737.europe-central2.run.app"

token = requests.get(url)

# Decrypt at runtime
decrypted_api_key = f.decrypt(token.text).decode()

# Now you can use the decrypted API key in OpenAI API calls

print("API key successfully decrypted and loaded!")
client = OpenAI(
    # API key of ELM
    api_key= decrypted_api_key
)

def gpt(messages:list, printChunk = True, model = 'gpt-4o'):
    """Choose the gpt model used for generation
    """
    if(model=='gpt-3.5-turbo'):
        return gpt_35_api_stream(messages, printChunk)
    elif(model=='gpt-4o'):
        return gpt_4o_api_stream(messages, printChunk)
    elif(model=='gpt-4o-mini'):
        return gpt_4o_mini_api_stream(messages, printChunk)
    elif(model=='gpt-o3-mini'):
        return gpt_o3_mini_api_stream(messages, printChunk)

def gpt_35_api_stream(messages: list, printChunk = True):
    """Create response for provided chat message (stream) using gpt3.5-turbo

    Args:
        messages (list): Full chat message
    """
    stream = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        stream=True,
    )
    response = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            if(printChunk):
                print(chunk.choices[0].delta.content, end="", flush=True)
            response.append(chunk.choices[0].delta.content)

    return "".join(str(element) for element in response)

def gpt_4o_api_stream(messages: list, printChunk = True):
    """Create response for provided chat message (stream) using gpt4o

    Args:
        messages (list): Full chat message
        printChunk (int): Decide whether print the output of gpt. 1 means yes and 0 means no.
    """
    stream = client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        stream=True,
    )
    response = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            if(printChunk):
                print(chunk.choices[0].delta.content, end="", flush=True)
            response.append(chunk.choices[0].delta.content)

    return "".join(str(element) for element in response)

def gpt_4o_mini_api_stream(messages: list, printChunk=True):
    """Create response for provided chat message (stream) using gpt-4omini.

    Args:
        messages (list): Full chat message
        printChunk (bool): Decide whether to print the output of GPT. True means yes.
    """
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            stream = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                stream=True,
                timeout=60
            )
            response = []

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    if(printChunk):
                        print(chunk.choices[0].delta.content, end="", flush=True)
                    response.append(chunk.choices[0].delta.content)

            return "".join(str(element) for element in response)
    
            return full_response

        except (openai.error.APIError, openai.error.Timeout, openai.error.APIConnectionError) as e:
            retry_count += 1
            print(f"\n[Error] API error occurred: {e}. Retrying... ({retry_count}/{max_retries})")
            time.sleep(2 ** retry_count)  # Exponential backoff

        except Exception as e:
            print(f"\n[Error] Unexpected error: {e}")
            break

    return "[Error] Failed to complete the request after multiple attempts."

def gpt_o3_mini_api_stream(messages: list, printChunk=True):
    """Create response for provided chat message (stream) using gpt-o3mini.

    Args:
        messages (list): Full chat message
        printChunk (bool): Decide whether to print the output of GPT. True means yes.
    """
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            stream = client.chat.completions.create(
                model='gpt-o3-mini',
                messages=messages,
                stream=True,
                timeout=60
            )
            response = []

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    if(printChunk):
                        print(chunk.choices[0].delta.content, end="", flush=True)
                    response.append(chunk.choices[0].delta.content)

            return "".join(str(element) for element in response)
    
            return full_response

        except (openai.error.APIError, openai.error.Timeout, openai.error.APIConnectionError) as e:
            retry_count += 1
            print(f"\n[Error] API error occurred: {e}. Retrying... ({retry_count}/{max_retries})")
            time.sleep(2 ** retry_count)  # Exponential backoff

        except Exception as e:
            print(f"\n[Error] Unexpected error: {e}")
            break

    return "[Error] Failed to complete the request after multiple attempts."


if __name__ == '__main__':
    print("Welcome to the AI Dungeon! You may use /help to check some commands useful for the game. Now please input your character name:")
    player = Character()
    story = Story()
    user_input = input()
    if(user_input.startswith("/read")):
        user_input = command_input(player, story, uinput=user_input)
        loadStory(player, story)
    else:
        player.name = user_input
        startDM(player, story)
        # startFirstTrade(player, story)
        startStory(player, story)
    while True:
        if(player.hp <= 0):
            print("Your HP is 0. Game over.")
            break
        event_type = checkEvent(player, story)
        if("encounter" in event_type.lower()):
            encounter(player, story)
        elif("battle" in event_type.lower()):
            battle(player, story)
        elif("event" in event_type.lower()):
            event(player, story)
        elif("trade" in event_type.lower()):
            trade(player, story)
        elif("none" in event_type.lower()):
            continueStory(player, story)
    
            
            

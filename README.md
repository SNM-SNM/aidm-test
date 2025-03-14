# aidm-test

## What is this?

This is my fourth-year Informatics Honours Project, "AI Dungeon Master". This project is a playable text-game in where an AI develops story outcomes based on your choices. The primary purpose of this research is to acquire useful feedback from users like you in order to evaluate how good the game is and improve the game.

## 📌 Installation

Git or download all files above. Make sure you have **Python 3.8+** installed on your system and a connection to the internet.

### Install Dependencies
Open your terminal. Run the following command to install all required packages:
```sh
pip install -r requirements.txt
```

### To start the game, go into aidm-test folder and execute:
```sh
python aidm.py
```

## 👍How to play
After running the game and inputting your character name, the game begins and the AI DM will start storytelling. The LLM will generates the world background and provided you with characters to choose. Your story then begins, and you may input your action when the AI DM tells you what you would like to do next. The event outcomes would be based on your choice and random dice-rolling (based on your character's attributes).

To better improve the game experience, there are some helper-commands in the game that you may use to review and save your character's info and the story. 
```sh
### Available commands:
/help -> Shows all commands
/me -> Shows the character information of the player
/save [file_name] -> Save the story so far into 2 txt file (story and character info).
/read [file_name] -> (Might not work perfectly) Load a saved game from 2 txt file (story and character info). 
/events -> Shows key events happened so far(in a summarization-way, would be usful for those who don't want to read a tons of paragraphs but just want to get a brief idea of what happened)
/rule [rule_type] [new_value] -> Update the game rule
```

## ☑️Feedback
If you may, engage in a user study and fill the [survey](https://forms.office.com/e/d8gfynZGD7) to evaluate the game. You may rate the game based on how well the AI DM is achieving these tasks as a dungeon master:
  - General information - How would you rate your overall experience with the AI DM?
  - World Building - How well did the AI describe the game world, including its geography, cultures, and history?
  - Storytelling - How engaging was the story crafted by the AI?
  - Rule Adjudication - How well did the AI DM interpret and enforce game rules (dice rolling) fairly?
  - NPC Management - How distinct and engaging were the NPCs controlled by the AI?
  - Encounter & Battle Design - How well did the AI create combats, encounters, and challenges?
  - Tracking Progress - How well did the AI track your character's progress, skills, and story continuity?
  - Feedback and Improvement - Did the AI adapt to your playstyle and choices (input) over time?

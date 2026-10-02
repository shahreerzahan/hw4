# AI Prompts – Homework 4

Record of what I asked the AI to do for each problem.

## Problem 1

### Prompt 1 – Download the data

> Working on Homework 4 for AI for Managers in the hw4 folder.
>
> First, from the following webpage (https://zlisto.github.io/mgt_409_fa26/hw4/p1.html), download the data.zip and put it in the hw4 folder; unzip in hw4 as well.

### Prompt 2 – Set up the project skeleton

> I'm starting Homework 4: a Campus Customs shop website with a React + Vite + TypeScript front end and a Python FastAPI backend whose chatbot is a PydanticAI agent using GPT through Portkey. Set up the project skeleton only, no features yet.
>
> 1. In this hw4 folder, create frontend/, backend/prompts/, and output/app_check_images/. The data/ folder is already here; don't change it.
>
> 2. Create .gitignore FIRST with: .env, data/, .venv/, node_modules/, \_\_pycache\_\_/, *.db, .DS_Store. Don't ignore png files in general, because output/app_check_images/ must be committed.
>
> 3. Create .env.example with PORTKEY_API_KEY=your-portkey-api-key-here and MODEL_NAME=gpt-5.6-luna. My real key is already in .env; never print it.
>
> 4. Python: create .venv, install fastapi uvicorn pydantic-ai portkey-ai python-dotenv bcrypt, and save requirements.txt in the hw4 root.
>
> 5. Front end: check node -v, then scaffold a Vite React TypeScript app inside frontend/ and run npm install.
>
> 6. Create AI_prompts.md with a heading for each of Problems 1 to 13, and a placeholder README.md.
>
> 7. Write backend/test_portkey.py that loads .env and makes one tiny Portkey call, run it, show me the reply, then delete the file.
>
> 8. git init, commit, add this remote and push: https://github.com/shahreerzahan/hw4.git. Show me git status and confirm .env and data/ are not tracked.

### Prompt 3 – Record the prompts

> Fill in the Problem 1 with the prompt I have already used.

## Problem 2

### Prompt 1 – Analyze the database

> Problem 2: Analyze the database
>
> Look inside 'data/campus_customs.db'
>
> List every table and its columns with types, and show 2 sample rows from catalogue, inventory, and users (hide the password hash values). Tell me which password hashing method the users table uses, because my login must match it so the test user test@campuscustoms.yale.edu can log in.
>
> Then create 'output/harness.md' with a "Database" section: each table, its fields, and one short line per field on why it matters for the shop or the chatbot. Commit and push.

## Problem 3

### Prompt 1 – Build the website

> Problem 3: Build the Campus Customs website
>
> For the front end, use React + Vite + TypeScript. Put a nav bar at the top with Home, Products, About Us, Log in, and Create account.
>
> For Home and About Us, use the wording style of yalebulldogblue.com but write the text in my own voice, not copied. I usually write in a welcoming, vibrant tone.
>
> On the Products page, show the product images and basic info (name, price, short description) from the database. When I click a product, it should open its own page with a big image on one side and the full details (description, price, sizes/stock) on the other.
>
> Add a chat box in the bottom right corner. It doesn't need to work yet, just a placeholder for now.
>
> Also start a simple FastAPI app in backend/main.py to serve the products and images from the database.
>
> When done, start everything so I can see it in the browser, then commit and push.

### Prompt 2 – Redesign the front end

> Let's rework the frontend of the website - the font should be Roboto, I expect the color tone to be earth tone; also, it should show Dan the Bulldog somewhere; the design should be modern, minimalistic, with white spaces so that it looks spectacular.

### Prompt 3 – Remove product photo backgrounds

> When I am checking out some of the products, they seem to have a black background on their back; bg remove from all the products so that it's a seamless and premium experience for the customers.

### Prompt 4 – Make the backgrounds transparent

> By Background removal, I meant to remove the black bg as shown in the images; not making the background white; re-do the work. if you can, remove the black and I do not want white background; I want it to be transparent

(Attached three screenshots of product photos still showing black and white backgrounds.)

### Prompt 5 – Navy collar for Dan

> Can you make Dan's Collar belt to be blue in stead of green? as given in the phto.

(Attached a photo of Handsome Dan wearing a navy Yale bandana.)

### Prompt 6 – Navy accent color

> In stead of orange/reddish, can you make the colors go with navy blue (#1F2E4D)?

(Attached a screenshot of the Home page headline with the orange accent.)

## Problem 4

### Prompt 1 – Create account and log in

> Problem 4: Add create account and log in.
>
> Build a normal create-account / login flow.
>
> Create account should ask for first name, last name, email, password, and confirm password. Log in should ask for email and password.
>
> New accounts should be saved in the users table. Please store passwords securely so no one can read them, and make sure it works with the existing hashed passwords in the database.
>
> Test it: log in with the test user (test@campuscustoms.yale.edu / password), then create a new account and make sure that one can log in too.
>
> Then add a section to output/harness.md explaining how login works: what we save for each user and how passwords are protected.
>
> Commit and push when done.

### Prompt 2 – Record the prompts

> add the respective prompts to AI_prompts.md if not added yet.

### Prompt 3 – Fix the test user login

> The test user login isn't working. Can you check how the existing passwords are stored and fix it?
>
> I want the password to be: password
>
> Fix it and I will try again.

(Attached a screenshot of the login form showing "Failed to fetch".)

## Problem 5

### Prompt 1 – PydanticAI agent backend

> Problem 5: PydanticAI agent backend
>
> Make the chatbot work using a PydanticAI agent behind FastAPI, like I did in Homework 3.
>
> Keep the agent as four files in the backend folder:
>
> • backend/prompts/prompt.md — system prompt (grow this same file later)
> • backend/agent.py — agent entry / wiring
> • backend/tools.py — tools the agent can call
> • backend/models.py — Pydantic / PydanticAI structured types
>
> In main.py, add a chat route so that when I type a message in the chat box on the website, the agent replies. Use my Portkey key from .env and gpt-5.6-luna.
>
> In prompt.md, give the agent a friendly Campus Customs voice and some basic safety rules. In models.py, add types for chat replies and product cards.
>
> Then add a section to output/harness.md explaining how the website talks to FastAPI and how the agent is loaded (prompt file and model).
>
> Make sure the backend runs from the backend folder with: uvicorn main:app --reload --port 8000
>
> Test it by sending a message in the chat box, then commit and push.

## Problem 6

### Prompt 1 – Product info and stock tools

> Problem 6: product info and stock
>
> Give the agent tools to look up real info from 'campus_customs.db':
>
> • Product description
> • Price
> • How many are in stock (by size when the customer asks)
>
> The agent must always use the database and never make up prices or quantities. If a size is out of stock, it should say so clearly.
>
> Update prompt.md so the agent knows to use these tools for price and stock questions, and add the return types for the tools in models.py.
>
> Then add a section to output/harness.md listing each tool and explaining which fields I chose for the results and why.
>
> Test it in the chat box by asking about a product's price and stock for a size, then commit and push.

## Problem 7

### Prompt 1 – Chat search that updates the page

> Problem 7: Chat search that updates the page
>
> When a customer asks about a type of item, like "what hoodies do you have?", the agent should search the catalogue and the website should dynamically show the matching items as product cards (image, name, price, short info) - a neat feature.
>
> The agent should return the matching products in a structured format, and the front end should display them on the page.
>
> Clicking any of these cards should still open the single product page from Problem 3.
>
> Update prompt.md and output/harness.md to explain how the search results get from the agent to the page.
>
> Test it by asking "what hoodies do you have?" in the chat, then commit and push.

## Problem 8

### Prompt 1 – Customer memory

> Problem 8: Customer memory
>
> When a shopper is logged in, save their chat history in the database (in a new table) and load it again when they come back. Guests can still chat, but their history doesn't need to be saved.
>
> The agent should know who is chatting (name and email). Pass that in using agent deps.
>
> Also pass the page the shopper is on, so if they're on a product page and ask "do you have this in pink?", the agent knows which product they mean.
>
> Then add a section to output/harness.md explaining how chat history is saved, what customer info the agent sees, and how the page info is passed.
>
> Test it: log in, chat, log out, and back in to see the history, and ask "do you have this in another color?" on a product page. Commit and push.

## Problem 9

_TODO_

## Problem 10

_TODO_

## Problem 11

_TODO_

## Problem 12

_TODO_

## Problem 13

_TODO_

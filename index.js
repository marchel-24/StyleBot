// index.js
require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const Groq = require('groq-sdk');
const { QuickDB } = require('quick.db');

// --- 1. Initialize Database ---
const db = new QuickDB();

// --- 2. Define Default User Profile ---
const defaultProfile = {
    gender: "not specified",
    style: "not specified",
    wardrobe: [],
    likes: [],
    dislikes: []
};

// --- 3. Initialize Groq AI Client ---
const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY
});

// --- 4. Initialize Discord Bot Client ---
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent, 
    ]
});

// --- 5. Define the LLM Agent Function (Styl-E) ---
async function getGroqChatCompletion(userMessage, userProfile) {
    
    const profileContext = `
--- USER'S PROFILE ---
Gender: ${userProfile.gender}
Preferred Style: ${userProfile.style}
Their Wardrobe: ${userProfile.wardrobe.join(', ') || 'empty'}
Likes: ${userProfile.likes.join(', ') || 'none'}
Dislikes: ${userProfile.dislikes.join(', ') || 'none'}
--- END PROFILE ---

Use this profile context to give a highly personalized answer to the user's request: "${userMessage}"
`;

    try {
        const completion = await groq.chat.completions.create({
            model:"llama-3.1-8b-instant",
            temperature: 0.8,
            max_tokens: 1024,
            top_p: 1,
            stream: false,
            messages: [
                {
                    role: "system",
                    content: `
You are **Styl-E**, a warm, confident, and trend-savvy virtual fashion stylist.
Your mission is to give friendly, clear, and stylish advice that makes people feel good and confident.

You excel at:
1. **Outfit Crafting:** Combine user-provided clothing items into complete, fashionable looks and explain *why* they work.
2. **Specific Advice:** Help users pick clothes for their body type, occasion, or vibe — always positive, inclusive, and practical.
3. **Expertise:** You're fluent in streetwear, minimalist, smart casual, vintage, and techwear styles.
4. **Tips & Tricks:** Offer clever insights on layering, colors, accessories, and balance.
5. **OOTD:** If asked for an "Outfit of the Day", ask clarifying questions first like weather or occasion, then build a killer look.

Your tone: Energetic, stylish, and encouraging — like a best friend with impeccable fashion sense.
Answer in a clear and well-formatted style using emojis and markdown to make it fun to read.
                    `
                },
                { role: "user", content: profileContext }
            ]
        });

        const rawReply = completion.choices[0]?.message?.content || "Hmm, I couldn’t think of anything stylish right now!";
        return `✨ **Styl-E Says:**\n${rawReply}\n\n💬 *Ask me again anytime for outfit inspo or style tips!* 👗👟`;
    } catch (error) {
        console.error("Error calling Groq API:", error);
        return "⚠️ Oops! Something went wrong while contacting the fashion oracle. Try again later.";
    }
}

// --- 6. Set up Discord Bot Event Listeners ---

client.on('clientReady', () => {
    console.log(`🪩 Logged in as ${client.user.tag}! Ready to style the world.`);
});

client.on('messageCreate', async (message) => {
    if (message.author.bot) return; 
    if (!message.mentions.has(client.user)) return;

    console.log(`[${message.author.tag}] ${message.content}`);
    await message.channel.sendTyping();

    const userId = message.author.id;
    const userMessage = message.content.replace(/<@!?\d+>/g, '').trim();
    
    let profile = await db.get(userId) || defaultProfile;

    const args = userMessage.split(' ');
    const command = args.shift().toLowerCase(); 
    const value = args.join(' '); 

    let replyMessage = ""; 

    switch (command) {
        case '!help':
            replyMessage = `
Hey! Here's how you can use my memory:
**!myprofile** - See all your saved info.
**!setgender [gender]** - Set your gender.
**!setstyle [style]** - Set your preferred style.
**!clearstyle** - Remove your saved style preference.
**!additem [item]** - Add a piece of clothing to your virtual wardrobe.
**!removeitem [item]** - Remove an item from your wardrobe.
**!addlike [like]** - Add a color, brand, or style you like.
**!removelike [like]** - Remove a specific like.
**!adddislike [dislike]** - Add something you don't like.
**!removedislike [dislike]** - Remove a specific dislike.
**!resetprofile** - Reset all your info.
            `;
            break;

        case '!myprofile':
            replyMessage = `
Here's what I have for you, **${message.author.username}**:
- **Gender:** ${profile.gender}
- **Style:** ${profile.style}
- **Wardrobe:** ${profile.wardrobe.join(', ') || 'empty'}
- **Likes:** ${profile.likes.join(', ') || 'none'}
- **Dislikes:** ${profile.dislikes.join(', ') || 'none'}
            `;
            break;

        case '!setgender':
            profile.gender = value;
            await db.set(userId, profile);
            replyMessage = `Got it! I've set your gender to: **${value}**`;
            break;

        case '!setstyle':
            profile.style = value;
            await db.set(userId, profile);
            replyMessage = `Love it! Your preferred style is now: **${value}**`;
            break;
            
        case '!clearstyle':
            profile.style = "not specified";
            await db.set(userId, profile);
            replyMessage = `Got it! I've cleared your style preference.`;
            break;

        case '!additem':
            if (value && !profile.wardrobe.includes(value)) {
                profile.wardrobe.push(value);
                await db.set(userId, profile);
                replyMessage = `Added **${value}** to your wardrobe! 👕`;
            } else if (!value) {
                replyMessage = "You need to tell me *what* to add! (e.g., `!additem blue jeans`)";
            } else {
                replyMessage = `You already have **${value}** in your wardrobe.`;
            }
            break;

        case '!removeitem':
            if (value && profile.wardrobe.includes(value)) {
                profile.wardrobe = profile.wardrobe.filter(item => item !== value);
                await db.set(userId, profile);
                replyMessage = `Removed **${value}** from your wardrobe.`;
            } else if (!value) {
                replyMessage = "You need to tell me *what* to remove! (e.g., `!removeitem blue jeans`)";
            } else {
                replyMessage = `You don't have **${value}** in your wardrobe.`;
            }
            break;

        case '!addlike':
            if (value && !profile.likes.includes(value)) {
                profile.likes.push(value);
                await db.set(userId, profile);
                replyMessage = `Noted! You like **${value}**.`;
            } else if (!value) {
                replyMessage = "You need to tell me *what* you like!";
            } else {
                replyMessage = `You already have **${value}** in your likes.`;
            }
            break;

        case '!removelike':
            if (value && profile.likes.includes(value)) {
                profile.likes = profile.likes.filter(item => item !== value);
                await db.set(userId, profile);
                replyMessage = `Removed **${value}** from your likes.`;
            } else if (!value) {
                replyMessage = "You need to tell me *what* to remove from your likes!";
            } else {
                replyMessage = `You don't have **${value}** in your likes.`;
            }
            break;

        case '!adddislike':
            if (value && !profile.dislikes.includes(value)) {
                profile.dislikes.push(value);
                await db.set(userId, profile);
                replyMessage = `Okay, I'll avoid **${value}**.`;
            } else if (!value) {
                replyMessage = "You need to tell me *what* you dislike!";
            } else {
                replyMessage = `You already have **${value}** in your dislikes.`;
            }
            break;

        case '!removedislike':
            if (value && profile.dislikes.includes(value)) {
                profile.dislikes = profile.dislikes.filter(item => item !== value);
                await db.set(userId, profile);
                replyMessage = `Removed **${value}** from your dislikes.`;
            } else if (!value) {
                replyMessage = "You need to tell me *what* to remove from your dislikes!";
            } else {
                replyMessage = `You don't have **${value}** in your dislikes.`;
            }
            break;
        
        case '!resetprofile':
            await db.set(userId, defaultProfile);
            replyMessage = `Your profile has been reset!`;
            break;
    }

    if (replyMessage) {
        await message.reply(replyMessage);
    } else {
        const aiResponse = await getGroqChatCompletion(userMessage, profile);
        
        if (aiResponse.length > 2000) {
            const chunks = aiResponse.match(/[\s\S]{1,1990}/g);
            for (const chunk of chunks) {
                await message.reply(chunk);
            }
        } else {
            await message.reply(aiResponse);
        }
    }
});

// --- 7. Log in to Discord ---
client.login(process.env.DISCORD_BOT_TOKEN);
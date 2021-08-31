const fs = require("fs");
const { Client, Collection, Intents } = require("discord.js");
require("dotenv").config();

class Bot {
  constructor() {
    this.client = new Client({ intents: [Intents.FLAGS.GUILDS] });
    this.client.commands = new Collection();
    const commandFiles = fs
      .readdirSync("./commands")
      .filter((file) => file.endsWith(".js"));

    for (const file of commandFiles) {
      const command = require(`./commands/${file}`);
      this.client.commands.set(command.data.name, command);
    }

    for (const file of commandFiles) {
      const command = require(`./commands/${file}`);
      // Set a new item in the Collection
      // With the key as the command name and the value as the exported module
      this.client.commands.set(command.data.name, command);
    }

    this.client.on("ready", async () => {
      console.log(`Logged in as ${this.client.user.tag}!`);
      // Get the server from the bot
      this.guild = await this.client.guilds.fetch(process.env.DISCORD_GUILD_ID);
      // Get the role from the server
      this.memberRole = await this.guild.roles.fetch(
        process.env.DISCORD_MEMBER_ROLE_ID
      );
    });

    this.client.on("interactionCreate", async (interaction) => {
      if (!interaction.isCommand()) return;

      const command = this.client.commands.get(interaction.commandName);

      if (!command) return;

      try {
        await command.execute(interaction);
      } catch (error) {
        console.error(error);
        return interaction.reply({
          content: "There was an error while executing this command!",
          ephemeral: true,
        });
      }
    });
  }

  init() {
    this.client.login(process.env.DISCORD_TOKEN);
  }
}

module.exports = Bot;

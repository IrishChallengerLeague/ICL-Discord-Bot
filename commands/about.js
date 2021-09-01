const { SlashCommandBuilder } = require("@discordjs/builders");
const { Interaction, MessageEmbed } = require("discord.js");
const package = require("../package.json");

const aboutEmbed = new MessageEmbed()
  .setColor("#427c28")
  .addField(
    `ICL Bot v${package.version}`,
    "Built by <@125033487051915264>",
    true
  );

module.exports = {
  data: new SlashCommandBuilder()
    .setName("about")
    .setDescription("Replies with bot information and version"),
  /**
   * @param {Interaction} interaction
   */
  async execute(interaction) {
    return interaction.reply({ embeds: [aboutEmbed] });
  },
};

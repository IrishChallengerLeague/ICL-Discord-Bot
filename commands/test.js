const { SlashCommandBuilder } = require("@discordjs/builders");
const { Permissions, Interaction } = require("discord.js");

module.exports = {
  data: new SlashCommandBuilder()
    .setName("test")
    .setDescription("Used for testing random functions"),
  /**
   * @param {Interaction} interaction
   */
  async execute(interaction) {
    let team1Channel = await interaction.guild.channels.create("test_team", {
      type: "GUILD_VOICE",
      parent: "787811785973432352", // Channel Category
      permissionOverwrites: [
        {
          id: "743042118041469008", // Guild ID aka @everyone
          deny: [Permissions.FLAGS.CONNECT],
        },
        {
          id: "125033487051915264",
          allow: [Permissions.FLAGS.VIEW_CHANNEL, Permissions.FLAGS.CONNECT],
        },
      ],
      reason: "Match Start",
    });
    return interaction.reply("Function tested");
  },
};

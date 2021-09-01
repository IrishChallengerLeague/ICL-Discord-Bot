const express = require("express");
const bodyParser = require("body-parser");
const cookieParser = require("cookie-parser");
const cookieSession = require("cookie-session");
const passport = require("passport");
const faceitStrategy = require("passport-faceit").Strategy;
const DiscordPassport = require("discord-passport");
const jwt = require("jsonwebtoken");
const axios = require("axios").default;
const { PrismaClient } = require("@prisma/client");
const Bot = require("./bot");
const { Permissions } = require("discord.js");

const prisma = new PrismaClient();

let app = express();

let liveMatches = [];

let discord = new Bot();
discord.init();

require("dotenv").config();

// Middlewares
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());
app.use(
  cookieSession({
    name: "session",
    secret: process.env.COOKIE_SECRET,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
  })
);
app.use(passport.initialize());

passport.use(
  new faceitStrategy(
    {
      clientID: process.env.FACEIT_CLIENT_ID,
      clientSecret: process.env.FACEIT_CLIENT_SECRET,
    },
    function (accessToken, refreshToken, params, profile, done) {
      const userData = jwt.decode(params.id_token);
      done(null, {
        faceitId: userData.guid,
        faceitAvatar: userData.picture,
        faceitEmail: userData.email,
        faceitNickname: userData.nickname,
      });
    }
  )
);

passport.serializeUser(function (user, done) {
  done(null, user);
});

passport.deserializeUser(function (user, done) {
  done(null, user);
});

app.get("/auth/faceit", passport.authenticate("faceit"));

app.get(
  "/auth/faceit/callback",
  passport.authenticate("faceit", { failureRedirect: "/fail" }),
  async (req, res) => {
    // Successful authentication, redirect home.
    req.session.faceit_id = req.user.faceitId;

    let hubs = await axios.get(
      `https://open.faceit.com/data/v4/players/${req.user.faceitId}/hubs?offset=0&limit=100`,
      {
        headers: {
          Authorization: `Bearer ${process.env.FACEIT_API_KEY}`,
        },
      }
    );
    let foundHub = false;
    for (i = 0; i < hubs.data.items.length; i++) {
      if (
        hubs.data.items[i].hub_id === "d9dba8bd-6bf9-435f-bdbc-808ae42d21bd" || // Irish Challenger League
        hubs.data.items[i].hub_id === "6a1da082-546e-4f7d-bbe6-54a0e42b9981" || // ICL Valorant
        hubs.data.items[i].hub_id === "c43a3d74-5ddc-45bd-bca3-569c1ff5df51" // ICL 1v1
      ) {
        foundHub = true;
        break;
      }
    }
    if (foundHub) {
      // link account to database
      await prisma.users.upsert({
        where: {
          discord_id_faceit_id: {
            discord_id: req.session.discord_id,
            faceit_id: req.user.faceitId,
          },
        },
        update: {
          discord_id: req.session.discord_id,
          faceit_id: req.user.faceitId,
        },
        create: {
          discord_id: req.session.discord_id,
          faceit_id: req.user.faceitId,
        },
      });

      // Add member role to user and rename
      try {
        discord.guild.members.fetch(req.session.discord_id).then((member) => {
          member.roles.add(discord.memberRole);
          member.setNickname(
            req.user.faceitNickname,
            "Linked Discord and FACEIT account"
          );
        });
      } catch (e) {
        console.log(
          "Can't add role or set nickname for " + req.session.discord_id
        );
      }
      // redirect to success page
      console.log("Successfully Linked account to ICL");
    } else {
      // redirect to the fail page to join ICL and link to the hub
      console.log("Join the hub");
    }

    res.redirect("/");
  }
);

app.get("/auth/discord", async (req, res) => {
  var code = req.query.code;

  var passport = new DiscordPassport({
    code: code,
    client_id: "784871645483237386",
    client_secret: "yELxS2Rl7HDV9C8fOw8Ew7a5zMj0rG7j",
    redirect_uri: "http://92.131.241.34:3000/auth/discord",
    scope: ["identify", "guilds"],
  });

  await passport.open(); // Trades your code for an access token and gets the basic scopes for you.

  // Add Discord ID to session
  req.session.discord_id = passport.user.id;

  let inGuild = false;
  for (i = 0; i < passport.guilds.length; i++) {
    if (passport.guilds[i].id === "784164014687125544") {
      inGuild = true;
      break;
    }
  }

  if (inGuild) {
    res.redirect("/auth/faceit");
  } else {
    // page with join discord link
  }

  // Check if in Discord, if not in Discord, show invite link, if in the discord, move to FACEIT auth
});

app.get("/link", async (req, res) => {
  res.redirect(
    "https://discord.com/api/oauth2/authorize?client_id=784871645483237386&redirect_uri=http%3A%2F%2F92.131.241.34%3A3000%2Fauth%2Fdiscord&response_type=code&scope=identify%20guilds"
  );
});

app.post("/faceit", async (req, res) => {
  // Check header for valid key
  console.log(req.body);
  // Rewrite this code: https://github.com/IrishChallengerLeague/ICL-Discord-Bot/blob/e7b07dd77d4fcd6242e17bba143e5d6868c060ca/utils/server.py#L48
  switch (req.body.event) {
    case "match_status_ready":
      console.log("ready");
      console.log(req.body);
      // loop through each team and find the discord ids/
      // let team1Channel = await discord.guild.channels.create(
      //   req.body.payload.teams[0].name,
      //   {
      //     type: "GUILD_VOICE",
      //     parent: "787811785973432352", // Channel Category
      //     permissionOverwrites: [
      //       {
      //         deny: [Permissions.FLAGS.CONNECT],
      //       },
      //       {
      //         id: "125033487051915264",
      //         allow: [
      //           Permissions.FLAGS.VIEW_CHANNEL,
      //           Permissions.FLAGS.CONNECT,
      //         ],
      //       },
      //     ],
      //     reason: "Match Start",
      //   }
      // );
      break;
    case "match_status_finished":
    case "match_status_aborted":
    case "match_status_cancelled":
      console.log("Game over");
      console.log(req.body);
      break;
    default:
      break;
  }
  res.sendStatus(200);
});

app.listen(3000);

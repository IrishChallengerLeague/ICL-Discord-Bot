-- CreateTable
CREATE TABLE "Users" (
    "discord_id" TEXT NOT NULL,
    "faceit_id" TEXT NOT NULL,

    PRIMARY KEY ("discord_id", "faceit_id")
);

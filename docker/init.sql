-- Create UDF for level_for_xp
-- TODO: at some point should not require this.
-- TODO: maybe at some point in the future we don't need this file altogether.
DROP FUNCTION IF EXISTS level_for_xp;
CREATE FUNCTION level_for_xp RETURNS INTEGER SONAME 'libxp.so';

CREATE DATABASE IF NOT EXISTS `runelite`;
CREATE DATABASE IF NOT EXISTS `runelite-cache2`;
CREATE DATABASE IF NOT EXISTS `runelite-tracker`;

--
-- Tables for the database `runelite-cache2`
-- Obtained from ./cache-updater/schema.sql
--

CREATE TABLE IF NOT EXISTS `runelite-cache2`.`archive` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `archiveId` int(11) NOT NULL,
  `nameHash` int(11) NOT NULL,
  `crc` int(11) NOT NULL,
  `revision` int(11) NOT NULL,
  `hash` binary(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `archive_revision` (`archiveId`,`revision`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE IF NOT EXISTS `runelite-cache2`.`cache` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `revision` int(11) NOT NULL,
  `date` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `revision_date` (`revision`,`date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE IF NOT EXISTS `runelite-cache2`.`file` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `archive` int(11) NOT NULL,
  `fileId` int(11) NOT NULL,
  `nameHash` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `archive_file` (`archive`,`fileId`),
  CONSTRAINT `file_ibfk_1` FOREIGN KEY (`archive`) REFERENCES `archive` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `runelite-cache2`.`index` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cache` int(11) NOT NULL,
  `indexId` int(11) NOT NULL,
  `crc` int(11) NOT NULL,
  `revision` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `indexId` (`cache`,`indexId`,`revision`,`crc`) USING BTREE,
  CONSTRAINT `index_ibfk_1` FOREIGN KEY (`cache`) REFERENCES `cache` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE IF NOT EXISTS `runelite-cache2`.`index_archive` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `index` int(11) NOT NULL,
  `archive` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_index_archive` (`index`,`archive`) USING BTREE,
  KEY `archive` (`archive`) USING BTREE,
  CONSTRAINT `index_archive_ibfk_1` FOREIGN KEY (`index`) REFERENCES `index` (`id`),
  CONSTRAINT `index_archive_ibfk_2` FOREIGN KEY (`archive`) REFERENCES `archive` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Tables for `runelite-tracker`
-- Obtained from ./http-service/target/classes/net/runelite/http/service/xp/schema.sql
--

CREATE TABLE IF NOT EXISTS `runelite-tracker`.`player` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `tracked_since` timestamp NOT NULL DEFAULT current_timestamp(),
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp(),
  `rank` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)

) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `runelite-tracker`.`xp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `time` timestamp NOT NULL DEFAULT current_timestamp(),
  `player` int(11) NOT NULL,
  `attack_xp` int(11) NOT NULL,
  `defence_xp` int(11) NOT NULL,
  `strength_xp` int(11) NOT NULL,
  `hitpoints_xp` int(11) NOT NULL,
  `ranged_xp` int(11) NOT NULL,
  `prayer_xp` int(11) NOT NULL,
  `magic_xp` int(11) NOT NULL,
  `cooking_xp` int(11) NOT NULL,
  `woodcutting_xp` int(11) NOT NULL,
  `fletching_xp` int(11) NOT NULL,
  `fishing_xp` int(11) NOT NULL,
  `firemaking_xp` int(11) NOT NULL,
  `crafting_xp` int(11) NOT NULL,
  `smithing_xp` int(11) NOT NULL,
  `mining_xp` int(11) NOT NULL,
  `herblore_xp` int(11) NOT NULL,
  `agility_xp` int(11) NOT NULL,
  `thieving_xp` int(11) NOT NULL,
  `slayer_xp` int(11) NOT NULL,
  `farming_xp` int(11) NOT NULL,
  `runecraft_xp` int(11) NOT NULL,
  `hunter_xp` int(11) NOT NULL,
  `construction_xp` int(11) NOT NULL,
  `overall_xp` int(11) GENERATED ALWAYS AS (`attack_xp` + `defence_xp` + `strength_xp` + `hitpoints_xp` + `ranged_xp` + `prayer_xp` + `magic_xp` + `cooking_xp` + `woodcutting_xp` + `fletching_xp` + `fishing_xp` + `firemaking_xp` + `crafting_xp` + `smithing_xp` + `mining_xp` + `herblore_xp` + `agility_xp` + `thieving_xp` + `slayer_xp` + `farming_xp` + `runecraft_xp` + `hunter_xp` + `construction_xp`) VIRTUAL,
  `attack_level` int(11) GENERATED ALWAYS AS (level_for_xp(`attack_xp` AS `attack_xp`)) VIRTUAL,
  `defence_level` int(11) GENERATED ALWAYS AS (level_for_xp(`defence_xp` AS `defence_xp`)) VIRTUAL,
  `strength_level` int(11) GENERATED ALWAYS AS (level_for_xp(`strength_xp` AS `strength_xp`)) VIRTUAL,
  `hitpoints_level` int(11) GENERATED ALWAYS AS (level_for_xp(`hitpoints_xp` AS `hitpoints_xp`)) VIRTUAL,
  `ranged_level` int(11) GENERATED ALWAYS AS (level_for_xp(`ranged_xp` AS `ranged_xp`)) VIRTUAL,
  `prayer_level` int(11) GENERATED ALWAYS AS (level_for_xp(`prayer_xp` AS `prayer_xp`)) VIRTUAL,
  `magic_level` int(11) GENERATED ALWAYS AS (level_for_xp(`magic_xp` AS `magic_xp`)) VIRTUAL,
  `cooking_level` int(11) GENERATED ALWAYS AS (level_for_xp(`cooking_xp` AS `cooking_xp`)) VIRTUAL,
  `woodcutting_level` int(11) GENERATED ALWAYS AS (level_for_xp(`woodcutting_xp` AS `woodcutting_xp`)) VIRTUAL,
  `fletching_level` int(11) GENERATED ALWAYS AS (level_for_xp(`fletching_xp` AS `fletching_xp`)) VIRTUAL,
  `fishing_level` int(11) GENERATED ALWAYS AS (level_for_xp(`fishing_xp` AS `fishing_xp`)) VIRTUAL,
  `firemaking_level` int(11) GENERATED ALWAYS AS (level_for_xp(`firemaking_xp` AS `firemaking_xp`)) VIRTUAL,
  `crafting_level` int(11) GENERATED ALWAYS AS (level_for_xp(`crafting_xp` AS `crafting_xp`)) VIRTUAL,
  `smithing_level` int(11) GENERATED ALWAYS AS (level_for_xp(`smithing_xp` AS `smithing_xp`)) VIRTUAL,
  `mining_level` int(11) GENERATED ALWAYS AS (level_for_xp(`mining_xp` AS `mining_xp`)) VIRTUAL,
  `herblore_level` int(11) GENERATED ALWAYS AS (level_for_xp(`herblore_xp` AS `herblore_xp`)) VIRTUAL,
  `agility_level` int(11) GENERATED ALWAYS AS (level_for_xp(`agility_xp` AS `agility_xp`)) VIRTUAL,
  `thieving_level` int(11) GENERATED ALWAYS AS (level_for_xp(`thieving_xp` AS `thieving_xp`)) VIRTUAL,
  `slayer_level` int(11) GENERATED ALWAYS AS (level_for_xp(`slayer_xp` AS `slayer_xp`)) VIRTUAL,
  `farming_level` int(11) GENERATED ALWAYS AS (level_for_xp(`farming_xp` AS `farming_xp`)) VIRTUAL,
  `runecraft_level` int(11) GENERATED ALWAYS AS (level_for_xp(`runecraft_xp` AS `runecraft_xp`)) VIRTUAL,
  `hunter_level` int(11) GENERATED ALWAYS AS (level_for_xp(`hunter_xp` AS `hunter_xp`)) VIRTUAL,
  `construction_level` int(11) GENERATED ALWAYS AS (level_for_xp(`construction_xp` AS `construction_xp`)) VIRTUAL,
  `overall_level` int(11) GENERATED ALWAYS AS (`attack_level` + `defence_level` + `strength_level` + `hitpoints_level` + `ranged_level` + `prayer_level` + `magic_level` + `cooking_level` + `woodcutting_level` + `fletching_level` + `fishing_level` + `firemaking_level` + `crafting_level` + `smithing_level` + `mining_level` + `herblore_level` + `agility_level` + `thieving_level` + `slayer_level` + `farming_level` + `runecraft_level` + `hunter_level` + `construction_level`) VIRTUAL,
  `attack_rank` int(11) NOT NULL,
  `defence_rank` int(11) NOT NULL,
  `strength_rank` int(11) NOT NULL,
  `hitpoints_rank` int(11) NOT NULL,
  `ranged_rank` int(11) NOT NULL,
  `prayer_rank` int(11) NOT NULL,
  `magic_rank` int(11) NOT NULL,
  `cooking_rank` int(11) NOT NULL,
  `woodcutting_rank` int(11) NOT NULL,
  `fletching_rank` int(11) NOT NULL,
  `fishing_rank` int(11) NOT NULL,
  `firemaking_rank` int(11) NOT NULL,
  `crafting_rank` int(11) NOT NULL,
  `smithing_rank` int(11) NOT NULL,
  `mining_rank` int(11) NOT NULL,
  `herblore_rank` int(11) NOT NULL,
  `agility_rank` int(11) NOT NULL,
  `thieving_rank` int(11) NOT NULL,
  `slayer_rank` int(11) NOT NULL,
  `farming_rank` int(11) NOT NULL,
  `runecraft_rank` int(11) NOT NULL,
  `hunter_rank` int(11) NOT NULL,
  `construction_rank` int(11) NOT NULL,
  `overall_rank` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `player_time` (`player`,`time`),
  KEY `idx_time` (`time`),
  CONSTRAINT `fk_player` FOREIGN KEY (`player`) REFERENCES `player` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE USER IF NOT EXISTS 'runelite'@'%' IDENTIFIED BY 'ironmanbtw';
GRANT ALL ON `runelite`.* TO 'runelite'@'%';
GRANT ALL ON `runelite-tracker`.* TO 'runelite'@'%';
GRANT ALL ON `runelite-cache2`.* TO 'runelite'@'%';

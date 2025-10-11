--[[ 
🔥 Enhanced Character Management Server Script
Author: Aden (Enhanced Version)
Place this in ServerScriptService
]]

print("========================================")
print("[Character Server] 🚀 ENHANCED SCRIPT STARTING!")
print("========================================")

-- // Services
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")
local DataStoreService = game:GetService("DataStoreService")

-- // DataStore
local CharacterStore = DataStoreService:GetDataStore("CharacterDataV1")

-- // Discord Webhook
local WEBHOOK_URL = "https://discord.com/api/webhooks/1425875614367486043/YlA89HiL7gViaqQJuzi5CKRiXEHGXtIizLHvzZ2RJLNnItwXQ1cDH3u3Iqo1LoyU0jtJ"

-- Wait for Events folder
print("[Character Server] Waiting for Events folder...")
local events = ReplicatedStorage:WaitForChild("Events", 10)
if not events then
	error("[Character Server] ❌ EVENTS FOLDER NOT FOUND!")
end
print("[Character Server] ✅ Events folder found!")

-- Wait for each remote
print("[Character Server] Looking for RemoteEvents...")
local GetCharacterData = events:WaitForChild("GetCharacterData", 5)
local CreateCharacter = events:WaitForChild("CreateCharacter", 5)
local MarkCharacterDead = events:WaitForChild("MarkCharacterDead", 5)
local OpenCharacterUI = events:WaitForChild("OpenCharacterUI", 5)

if not GetCharacterData then error("[Character Server] ❌ GetCharacterData not found!") end
if not CreateCharacter then error("[Character Server] ❌ CreateCharacter not found!") end
if not MarkCharacterDead then error("[Character Server] ❌ MarkCharacterDead not found!") end
if not OpenCharacterUI then error("[Character Server] ❌ OpenCharacterUI not found!") end

print("[Character Server] ✅ All RemoteEvents found!")

-- // Functions

-- Send to Discord Webhook
local function sendToDiscord(title, description, color, fields)
	local success, err = pcall(function()
		local data = {
			embeds = {{
				title = title,
				description = description,
				color = color,
				fields = fields or {},
				timestamp = DateTime.now():ToIsoDate(),
				footer = {
					text = "Character Management System"
				}
			}}
		}

		HttpService:PostAsync(
			WEBHOOK_URL,
			HttpService:JSONEncode(data),
			Enum.HttpContentType.ApplicationJson,
			false
		)
	end)

	if not success then
		warn("[Character Server] ⚠️ Webhook error:", err)
	end
end

-- Load player data
local function loadPlayerData(userId)
	local success, data = pcall(function()
		return CharacterStore:GetAsync("Player_" .. userId)
	end)

	if success and data then
		print("[Character Server] 📂 Loaded data for user:", userId)
		return data
	else
		print("[Character Server] 📝 No existing data for user:", userId)
		return {
			currentCharacter = nil,
			pastCharacters = {}
		}
	end
end

-- Save player data
local function savePlayerData(userId, data)
	local success, err = pcall(function()
		CharacterStore:SetAsync("Player_" .. userId, data)
	end)

	if success then
		print("[Character Server] 💾 Data saved for user:", userId)
	else
		warn("[Character Server] ⚠️ Failed to save data:", err)
	end
end

-- // Get Character Data
GetCharacterData.OnServerEvent:Connect(function(player)
	print("========================================")
	print("[Character Server] 📡 DATA REQUEST FROM: " .. player.Name)
	print("========================================")

	local data = loadPlayerData(player.UserId)

	print("[Character Server] 📤 Sending data to client...")
	OpenCharacterUI:FireClient(player, data)
	print("[Character Server] ✅ Data sent!")
end)

-- // Create Character
CreateCharacter.OnServerEvent:Connect(function(player, characterInfo)
	print("========================================")
	print("[Character Server] 🎭 CHARACTER CREATION: " .. player.Name)
	print("========================================")

	if not characterInfo or not characterInfo.Name or not characterInfo.Backstory then
		warn("[Character Server] ⚠️ Invalid character data")
		return
	end

	-- Load player data
	local data = loadPlayerData(player.UserId)

	-- If they have a current character, move it to past
	if data.currentCharacter then
		table.insert(data.pastCharacters, data.currentCharacter)
	end

	-- Create new character
	local newCharacter = {
		Name = characterInfo.Name,
		Birthday = os.date("%B %d, %Y"),
		Backstory = characterInfo.Backstory,
		CreatedAt = os.time(),
		PlayerName = player.Name,
		PlayerId = player.UserId,
		Status = "Alive"
	}

	data.currentCharacter = newCharacter

	-- Save to DataStore
	savePlayerData(player.UserId, data)

	-- Send to Discord
	sendToDiscord(
		"🎭 New Character Created!",
		"A new character has been born into the world!",
		3066993, -- Green color
		{
			{name = "Character Name", value = newCharacter.Name, inline = true},
			{name = "Player", value = player.Name, inline = true},
			{name = "Birthday", value = newCharacter.Birthday, inline = true},
			{name = "Backstory", value = newCharacter.Backstory, inline = false}
		}
	)

	print("[Character Server] ✅ Character created and logged!")

	-- Send updated data back
	OpenCharacterUI:FireClient(player, data)
end)

-- // Mark Character as Dead (Permadeath)
MarkCharacterDead.OnServerEvent:Connect(function(player)
	print("========================================")
	print("[Character Server] ☠️ PERMADEATH EVENT: " .. player.Name)
	print("========================================")

	local data = loadPlayerData(player.UserId)

	if not data.currentCharacter then
		warn("[Character Server] ⚠️ No current character to mark as dead")
		return
	end

	-- Mark as dead and move to past
	data.currentCharacter.Status = "Deceased"
	data.currentCharacter.DeathDate = os.date("%B %d, %Y")
	table.insert(data.pastCharacters, data.currentCharacter)

	-- Send death notification to Discord
	sendToDiscord(
		"☠️ Character Death",
		"A character has met their end...",
		15158332, -- Red color
		{
			{name = "Character Name", value = data.currentCharacter.Name, inline = true},
			{name = "Player", value = player.Name, inline = true},
			{name = "Death Date", value = data.currentCharacter.DeathDate, inline = true},
			{name = "Backstory", value = data.currentCharacter.Backstory, inline = false}
		}
	)

	-- Remove current character
	data.currentCharacter = nil

	-- Save
	savePlayerData(player.UserId, data)

	print("[Character Server] ✅ Character marked as deceased")

	-- Send updated data back
	OpenCharacterUI:FireClient(player, data)
end)

-- // Cleanup on leave
Players.PlayerRemoving:Connect(function(player)
	print("[Character Server] 👋 Player leaving:", player.Name)
end)

print("========================================")
print("[Character Server] ✅✅✅ ALL SYSTEMS READY! ✅✅✅")
print("========================================")

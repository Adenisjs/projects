--[[
	CIA AUTOMATIONS SYSTEM V1
	Gamepass Handler with Animated Notifications
	
	HOW TO ADD MORE GAMEPASSES:
	1. Add a new entry to the GAMEPASSES table below
	2. Create the tool/item in ReplicatedStorage
	3. Optionally add hardcoded UserIds to HardcodedUsers
	4. The system handles the rest automatically!
	
	ADMIN COMMANDS:
	- !gamepassgive [username] [gamepass number] - Add a user to a gamepass whitelist
]]

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

-- ============================================
-- ADMIN CONFIGURATION
-- ============================================
local ADMIN_USER_ID = 62968064

-- ============================================
-- GAMEPASS CONFIGURATION
-- ============================================
local GAMEPASSES = {
	-- TEMPLATE: Copy this structure to add new gamepasses
	{
		GamepassId = 1505287469,
		ItemName = "Protest", -- Name of the tool in ReplicatedStorage
		DisplayName = "Protest Sign",
		Message = "We detected you have the protest sign gamepass!! It has been given to you",
		IconColor = Color3.fromRGB(52, 152, 219), -- Blue
		HardcodedUsers = { -- Add UserIds here to give them the item without needing the gamepass
			8802544916,
		},
	},
	{
		GamepassId = 953755057,
		ItemName = "Glock 22", -- Name of the tool in ReplicatedStorage
		DisplayName = "Glock 22",
		Message = "We detected you have the Glock 22 gamepass!! It has been given to you",
		IconColor = Color3.fromRGB(52, 152, 219), -- Blue
		HardcodedUsers = { -- Add UserIds here to give them the item without needing the gamepass
			467330362,
		},
	},
	{
		GamepassId = 953609235,
		ItemName = "M249", -- Name of the tool in ReplicatedStorage
		DisplayName = "M249",
		Message = "We detected you have the M249 gamepass!! It has been given to you",
		IconColor = Color3.fromRGB(52, 152, 219), -- Blue
		HardcodedUsers = { -- Add UserIds here to give them the item without needing the gamepass
			8802544916,
		},
	},
	{
		GamepassId = 953627117,
		ItemName = "M4A1", -- Name of the tool in ReplicatedStorage
		DisplayName = "M4A1",
		Message = "We detected you have the M4A1 gamepass!! It has been given to you",
		IconColor = Color3.fromRGB(52, 152, 219), -- Blue
		HardcodedUsers = { -- Add UserIds here to give them the item without needing the gamepass
			8802544916,
		},
	},
	{
		GamepassId = 953721144,
		ItemName = "RPG", -- Name of the tool in ReplicatedStorage
		DisplayName = "RPG",
		Message = "We detected you have the Rocket Launcher gamepass!! It has been given to you",
		IconColor = Color3.fromRGB(52, 152, 219), -- Blue
		HardcodedUsers = { -- Add UserIds here to give them the item without needing the gamepass
			8802544916,
		},
	},
}

-- ============================================
-- TRACKING
-- ============================================
local messageShown = {} -- Track which players have seen messages
local itemsGiven = {} -- Track which items have been given to prevent duplicates

-- ============================================
-- HELPER FUNCTIONS
-- ============================================
local function isHardcodedUser(userId, gamepassData)
	if not gamepassData.HardcodedUsers then return false end

	for _, hardcodedId in ipairs(gamepassData.HardcodedUsers) do
		if userId == hardcodedId then
			return true
		end
	end
	return false
end

local function playerHasAccess(player, gamepassData)
	-- Check if user is hardcoded first
	if isHardcodedUser(player.UserId, gamepassData) then
		return true
	end

	-- Otherwise check if they own the gamepass
	local success, hasPass = pcall(function()
		return MarketplaceService:UserOwnsGamePassAsync(player.UserId, gamepassData.GamepassId)
	end)

	return success and hasPass
end

local function getGamepassByNumber(number)
	if number >= 1 and number <= #GAMEPASSES then
		return GAMEPASSES[number]
	end
	return nil
end

local function sendSystemMessage(player, message, color)
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = "SystemMessage"
	screenGui.ResetOnSpawn = false
	screenGui.Parent = player:WaitForChild("PlayerGui")

	local messageFrame = Instance.new("Frame")
	messageFrame.Size = UDim2.new(0, 400, 0, 60)
	messageFrame.Position = UDim2.new(0.5, -200, 0, -100)
	messageFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 35)
	messageFrame.BorderSizePixel = 0
	messageFrame.Parent = screenGui

	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 10)
	corner.Parent = messageFrame

	local stroke = Instance.new("UIStroke")
	stroke.Color = color or Color3.fromRGB(52, 152, 219)
	stroke.Thickness = 2
	stroke.Parent = messageFrame

	local textLabel = Instance.new("TextLabel")
	textLabel.Size = UDim2.new(1, -20, 1, 0)
	textLabel.Position = UDim2.new(0, 10, 0, 0)
	textLabel.BackgroundTransparency = 1
	textLabel.Text = message
	textLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	textLabel.TextSize = 14
	textLabel.Font = Enum.Font.GothamBold
	textLabel.TextWrapped = true
	textLabel.Parent = messageFrame

	local slideIn = TweenService:Create(
		messageFrame,
		TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Position = UDim2.new(0.5, -200, 0, 20)}
	)

	slideIn:Play()
	task.wait(3)

	local slideOut = TweenService:Create(
		messageFrame,
		TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
		{Position = UDim2.new(0.5, -200, 0, -100)}
	)

	slideOut:Play()
	slideOut.Completed:Wait()
	screenGui:Destroy()
end

-- ============================================
-- NOTIFICATION SYSTEM
-- ============================================
local function createNotification(player, gamepassData)
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = "GamepassNotification"
	screenGui.ResetOnSpawn = false
	screenGui.Parent = player:WaitForChild("PlayerGui")

	-- Main Container
	local container = Instance.new("Frame")
	container.Name = "Container"
	container.Size = UDim2.new(0, 450, 0, 160)
	container.Position = UDim2.new(0.5, -225, -0.3, 0) -- Start off-screen
	container.BackgroundColor3 = Color3.fromRGB(30, 30, 35)
	container.BorderSizePixel = 0
	container.Parent = screenGui

	local containerCorner = Instance.new("UICorner")
	containerCorner.CornerRadius = UDim.new(0, 12)
	containerCorner.Parent = container

	local containerStroke = Instance.new("UIStroke")
	containerStroke.Color = gamepassData.IconColor
	containerStroke.Thickness = 2
	containerStroke.Transparency = 0.5
	containerStroke.Parent = container

	-- Header with Icon
	local header = Instance.new("Frame")
	header.Name = "Header"
	header.Size = UDim2.new(1, 0, 0, 40)
	header.BackgroundColor3 = Color3.fromRGB(40, 40, 45)
	header.BorderSizePixel = 0
	header.Parent = container

	local headerCorner = Instance.new("UICorner")
	headerCorner.CornerRadius = UDim.new(0, 12)
	headerCorner.Parent = header

	local icon = Instance.new("Frame")
	icon.Size = UDim2.new(0, 24, 0, 24)
	icon.Position = UDim2.new(0, 10, 0.5, -12)
	icon.BackgroundColor3 = gamepassData.IconColor
	icon.BorderSizePixel = 0
	icon.Parent = header

	local iconCorner = Instance.new("UICorner")
	iconCorner.CornerRadius = UDim.new(1, 0)
	iconCorner.Parent = icon

	local checkmark = Instance.new("TextLabel")
	checkmark.Size = UDim2.new(1, 0, 1, 0)
	checkmark.BackgroundTransparency = 1
	checkmark.Text = "✓"
	checkmark.TextColor3 = Color3.fromRGB(255, 255, 255)
	checkmark.TextSize = 18
	checkmark.Font = Enum.Font.GothamBold
	checkmark.Parent = icon

	local headerTitle = Instance.new("TextLabel")
	headerTitle.Size = UDim2.new(1, -50, 1, 0)
	headerTitle.Position = UDim2.new(0, 45, 0, 0)
	headerTitle.BackgroundTransparency = 1
	headerTitle.Text = "🎮 GAMEPASS DETECTED"
	headerTitle.TextColor3 = Color3.fromRGB(255, 255, 255)
	headerTitle.TextSize = 14
	headerTitle.Font = Enum.Font.GothamBold
	headerTitle.TextXAlignment = Enum.TextXAlignment.Left
	headerTitle.Parent = header

	-- Message Content
	local messageLabel = Instance.new("TextLabel")
	messageLabel.Size = UDim2.new(1, -30, 0, 70)
	messageLabel.Position = UDim2.new(0, 15, 0, 50)
	messageLabel.BackgroundTransparency = 1
	messageLabel.Text = gamepassData.Message
	messageLabel.TextColor3 = Color3.fromRGB(220, 220, 220)
	messageLabel.TextSize = 16
	messageLabel.Font = Enum.Font.Gotham
	messageLabel.TextWrapped = true
	messageLabel.TextXAlignment = Enum.TextXAlignment.Left
	messageLabel.TextYAlignment = Enum.TextYAlignment.Top
	messageLabel.Parent = container

	-- Footer
	local footer = Instance.new("Frame")
	footer.Name = "Footer"
	footer.Size = UDim2.new(1, 0, 0, 30)
	footer.Position = UDim2.new(0, 0, 1, -30)
	footer.BackgroundColor3 = Color3.fromRGB(25, 25, 30)
	footer.BorderSizePixel = 0
	footer.Parent = container

	local footerCorner = Instance.new("UICorner")
	footerCorner.CornerRadius = UDim.new(0, 12)
	footerCorner.Parent = footer

	local footerLabel = Instance.new("TextLabel")
	footerLabel.Size = UDim2.new(1, -20, 1, 0)
	footerLabel.Position = UDim2.new(0, 10, 0, 0)
	footerLabel.BackgroundTransparency = 1
	footerLabel.Text = "⚡ CIA AUTOMATIONS SYSTEM V1 | Created By Aden"
	footerLabel.TextColor3 = Color3.fromRGB(150, 150, 155)
	footerLabel.TextSize = 11
	footerLabel.Font = Enum.Font.GothamBold
	footerLabel.TextXAlignment = Enum.TextXAlignment.Center
	footerLabel.Parent = footer

	-- Animations
	local slideIn = TweenService:Create(
		container,
		TweenInfo.new(0.6, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
		{Position = UDim2.new(0.5, -225, 0.1, 0)}
	)

	local iconPulse = TweenService:Create(
		icon,
		TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut, -1, true),
		{Size = UDim2.new(0, 28, 0, 28)}
	)

	local glowPulse = TweenService:Create(
		containerStroke,
		TweenInfo.new(1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
		{Transparency = 0.2}
	)

	local fadeOut = TweenService:Create(
		container,
		TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
		{Position = UDim2.new(0.5, -225, -0.3, 0)}
	)

	local transparencyFade = TweenService:Create(
		container,
		TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In),
		{BackgroundTransparency = 1}
	)

	slideIn:Play()
	task.wait(0.2)
	iconPulse:Play()
	glowPulse:Play()

	task.wait(12)

	iconPulse:Cancel()
	glowPulse:Cancel()

	fadeOut:Play()
	transparencyFade:Play()
	fadeOut.Completed:Wait()
	screenGui:Destroy()
end

-- ============================================
-- ITEM GIVING SYSTEM (FIXED - NO DUPLICATES)
-- ============================================
local function giveItem(player, gamepassData)
	-- Create unique key for this player/gamepass combination
	local itemKey = player.UserId .. "_" .. gamepassData.GamepassId

	-- Check if we've already given this item to this player
	if itemsGiven[itemKey] then
		return -- Already given, skip
	end

	local gamepassFolder = game.ReplicatedStorage:FindFirstChild("GamepassItems")
	if not gamepassFolder then
		warn("CIA AUTOMATIONS: 'GamePassItems' folder not found in ReplicatedStorage!")
		return
	end

	local item = gamepassFolder:FindFirstChild(gamepassData.ItemName)
	if item then
		-- Only give to backpack, NOT to character (prevents duplication)
		local clone = item:Clone()
		clone.Parent = player.Backpack

		-- Mark this item as given
		itemsGiven[itemKey] = true
	else
		warn("CIA AUTOMATIONS: Item '" .. gamepassData.ItemName .. "' not found in GamePassItems folder!")
	end
end

-- ============================================
-- MOVEMENT DETECTION
-- ============================================
local function waitForPlayerMovement(player)
	local character = player.Character or player.CharacterAdded:Wait()
	local humanoidRootPart = character:WaitForChild("HumanoidRootPart")

	-- Store initial position
	local initialPosition = humanoidRootPart.Position
	local hasMovedThreshold = 5 -- studs movement required

	-- Wait until player moves significantly
	while true do
		task.wait(0.5)
		if not humanoidRootPart or not humanoidRootPart.Parent then break end

		local currentPosition = humanoidRootPart.Position
		local distance = (currentPosition - initialPosition).Magnitude

		if distance >= hasMovedThreshold then
			return true -- Player has moved
		end
	end

	return false
end

-- ============================================
-- MAIN GAMEPASS CHECKING
-- ============================================
local function checkGamepasses(player, showNotification)
	task.wait(10)

	-- Wait for the player to move before giving items
	waitForPlayerMovement(player)

	for _, gamepassData in ipairs(GAMEPASSES) do
		if playerHasAccess(player, gamepassData) then
			if showNotification and not messageShown[player.UserId .. "_" .. gamepassData.GamepassId] then
				createNotification(player, gamepassData)
				messageShown[player.UserId .. "_" .. gamepassData.GamepassId] = true
			end

			giveItem(player, gamepassData)
		end
	end
end

-- ============================================
-- ADMIN COMMAND SYSTEM
-- ============================================
local function handleAdminCommand(player, message)
	if player.UserId ~= ADMIN_USER_ID then return end

	local args = message:split(" ")
	local command = args[1]:lower()

	if command == "!gamepassgive" then
		if #args < 3 then
			sendSystemMessage(player, "❌ Usage: !gamepassgive [username] [gamepass number]", Color3.fromRGB(231, 76, 60))
			return
		end

		local targetUsername = args[2]
		local gamepassNumber = tonumber(args[3])

		if not gamepassNumber then
			sendSystemMessage(player, "❌ Invalid gamepass number!", Color3.fromRGB(231, 76, 60))
			return
		end

		local gamepassData = getGamepassByNumber(gamepassNumber)
		if not gamepassData then
			sendSystemMessage(player, "❌ Gamepass #" .. gamepassNumber .. " does not exist!", Color3.fromRGB(231, 76, 60))
			return
		end

		-- Find target player
		local targetPlayer = nil
		for _, plr in ipairs(Players:GetPlayers()) do
			if plr.Name:lower():match("^" .. targetUsername:lower()) then
				targetPlayer = plr
				break
			end
		end

		if not targetPlayer then
			sendSystemMessage(player, "❌ Player '" .. targetUsername .. "' not found!", Color3.fromRGB(231, 76, 60))
			return
		end

		-- Check if already in whitelist
		if isHardcodedUser(targetPlayer.UserId, gamepassData) then
			sendSystemMessage(player, "⚠️ " .. targetPlayer.Name .. " is already whitelisted for " .. gamepassData.DisplayName, Color3.fromRGB(241, 196, 15))
			return
		end

		-- Add to whitelist
		table.insert(gamepassData.HardcodedUsers, targetPlayer.UserId)

		sendSystemMessage(player, "✅ Added " .. targetPlayer.Name .. " to " .. gamepassData.DisplayName .. " whitelist!", Color3.fromRGB(46, 204, 113))

		-- Give them the item immediately
		giveItem(targetPlayer, gamepassData)
		createNotification(targetPlayer, gamepassData)

		print("✅ ADMIN ACTION: " .. player.Name .. " added " .. targetPlayer.Name .. " (ID: " .. targetPlayer.UserId .. ") to gamepass: " .. gamepassData.DisplayName)
	end
end

-- ============================================
-- PLAYER CONNECTION
-- ============================================
Players.PlayerAdded:Connect(function(player)
	-- Clear items given tracker when player joins
	for key in pairs(itemsGiven) do
		if key:match("^" .. player.UserId .. "_") then
			itemsGiven[key] = nil
		end
	end

	checkGamepasses(player, true)

	player.CharacterAdded:Connect(function(character)
		character:WaitForChild("Humanoid")
		task.wait(0.1)

		-- Clear items given tracker for respawn
		for key in pairs(itemsGiven) do
			if key:match("^" .. player.UserId .. "_") then
				itemsGiven[key] = nil
			end
		end

		-- Give items on respawn (without notification, without movement check)
		for _, gamepassData in ipairs(GAMEPASSES) do
			if playerHasAccess(player, gamepassData) then
				giveItem(player, gamepassData)
			end
		end
	end)

	-- Admin command listener
	player.Chatted:Connect(function(message)
		handleAdminCommand(player, message)
	end)
end)

-- Handle players already in game when script loads
for _, player in ipairs(Players:GetPlayers()) do
	checkGamepasses(player, true)

	player.CharacterAdded:Connect(function(character)
		character:WaitForChild("Humanoid")
		task.wait(0.1)

		-- Clear items given tracker for respawn
		for key in pairs(itemsGiven) do
			if key:match("^" .. player.UserId .. "_") then
				itemsGiven[key] = nil
			end
		end

		-- Give items on respawn (without notification, without movement check)
		for _, gamepassData in ipairs(GAMEPASSES) do
			if playerHasAccess(player, gamepassData) then
				giveItem(player, gamepassData)
			end
		end
	end)

	player.Chatted:Connect(function(message)
		handleAdminCommand(player, message)
	end)
end

print("✅ CIA AUTOMATIONS SYSTEM V1 - Loaded successfully!")
print("📋 Monitoring " .. #GAMEPASSES .. " gamepass(es)")
print("👑 Admin User ID: " .. ADMIN_USER_ID)

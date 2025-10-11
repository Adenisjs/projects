--[[ 
🎭 Enhanced Character Management Client UI
Author: Aden (Enhanced Version)
Place this in StarterPlayer > StarterPlayerScripts
]]

print("[Character Client] 🚀 Client script loading...")

-- // Services
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- // Events
local events = ReplicatedStorage:WaitForChild("Events")
local GetCharacterData = events:WaitForChild("GetCharacterData")
local CreateCharacter = events:WaitForChild("CreateCharacter")
local MarkCharacterDead = events:WaitForChild("MarkCharacterDead")
local OpenCharacterUI = events:WaitForChild("OpenCharacterUI")

-- // Variables
local mainGui
local currentData = {}
local currentTab = "current"

-- // Tween Info
local tweenInfo = TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local fastTween = TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

-- // Helper Functions

local function createTween(object, properties)
	return TweenService:Create(object, tweenInfo, properties)
end

local function animateButton(button)
	button.MouseEnter:Connect(function()
		createTween(button, {Size = button.Size + UDim2.new(0, 4, 0, 4)}):Play()
		createTween(button, {BackgroundColor3 = Color3.fromRGB(100, 200, 255)}):Play()
	end)

	button.MouseLeave:Connect(function()
		createTween(button, {Size = button.Size - UDim2.new(0, 4, 0, 4)}):Play()
		createTween(button, {BackgroundColor3 = Color3.fromRGB(70, 150, 255)}):Play()
	end)
end

-- // Create Main GUI
local function createMainUI()
	-- Remove existing GUI
	if playerGui:FindFirstChild("CharacterManagementUI") then
		playerGui.CharacterManagementUI:Destroy()
	end

	-- Create ScreenGui
	mainGui = Instance.new("ScreenGui")
	mainGui.Name = "CharacterManagementUI"
	mainGui.ResetOnSpawn = false
	mainGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	mainGui.Parent = playerGui

	-- Main Frame
	local mainFrame = Instance.new("Frame")
	mainFrame.Name = "MainFrame"
	mainFrame.Size = UDim2.new(0, 800, 0, 600)
	mainFrame.Position = UDim2.new(0.5, 0, 0.5, 0)
	mainFrame.AnchorPoint = Vector2.new(0.5, 0.5)
	mainFrame.BackgroundColor3 = Color3.fromRGB(25, 25, 35)
	mainFrame.BorderSizePixel = 0
	mainFrame.Visible = false
	mainFrame.Parent = mainGui

	-- Rounded corners
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 16)
	corner.Parent = mainFrame

	-- Shadow effect
	local shadow = Instance.new("ImageLabel")
	shadow.Name = "Shadow"
	shadow.Size = UDim2.new(1, 40, 1, 40)
	shadow.Position = UDim2.new(0.5, 0, 0.5, 0)
	shadow.AnchorPoint = Vector2.new(0.5, 0.5)
	shadow.BackgroundTransparency = 1
	shadow.Image = "rbxasset://textures/ui/GuiImagePlaceholder.png"
	shadow.ImageColor3 = Color3.fromRGB(0, 0, 0)
	shadow.ImageTransparency = 0.7
	shadow.ZIndex = 0
	shadow.Parent = mainFrame

	-- Header
	local header = Instance.new("Frame")
	header.Name = "Header"
	header.Size = UDim2.new(1, 0, 0, 80)
	header.BackgroundColor3 = Color3.fromRGB(35, 35, 50)
	header.BorderSizePixel = 0
	header.Parent = mainFrame

	local headerCorner = Instance.new("UICorner")
	headerCorner.CornerRadius = UDim.new(0, 16)
	headerCorner.Parent = header

	-- Title
	local title = Instance.new("TextLabel")
	title.Name = "Title"
	title.Size = UDim2.new(0.6, 0, 1, 0)
	title.Position = UDim2.new(0, 20, 0, 0)
	title.BackgroundTransparency = 1
	title.Text = "🎭 Character Management"
	title.TextColor3 = Color3.fromRGB(255, 255, 255)
	title.TextSize = 28
	title.Font = Enum.Font.GothamBold
	title.TextXAlignment = Enum.TextXAlignment.Left
	title.Parent = header

	-- Close Button
	local closeBtn = Instance.new("TextButton")
	closeBtn.Name = "CloseButton"
	closeBtn.Size = UDim2.new(0, 50, 0, 50)
	closeBtn.Position = UDim2.new(1, -60, 0.5, 0)
	closeBtn.AnchorPoint = Vector2.new(0, 0.5)
	closeBtn.BackgroundColor3 = Color3.fromRGB(255, 70, 70)
	closeBtn.Text = "✕"
	closeBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
	closeBtn.TextSize = 24
	closeBtn.Font = Enum.Font.GothamBold
	closeBtn.BorderSizePixel = 0
	closeBtn.Parent = header

	local closeBtnCorner = Instance.new("UICorner")
	closeBtnCorner.CornerRadius = UDim.new(0, 12)
	closeBtnCorner.Parent = closeBtn

	closeBtn.MouseButton1Click:Connect(function()
		createTween(mainFrame, {Size = UDim2.new(0, 0, 0, 0)}):Play()
		wait(0.3)
		mainFrame.Visible = false
		mainFrame.Size = UDim2.new(0, 800, 0, 600)
	end)

	-- Tab Buttons Container
	local tabContainer = Instance.new("Frame")
	tabContainer.Name = "TabContainer"
	tabContainer.Size = UDim2.new(1, -40, 0, 50)
	tabContainer.Position = UDim2.new(0, 20, 0, 90)
	tabContainer.BackgroundTransparency = 1
	tabContainer.Parent = mainFrame

	-- Current Tab Button
	local currentTabBtn = Instance.new("TextButton")
	currentTabBtn.Name = "CurrentTab"
	currentTabBtn.Size = UDim2.new(0.5, -5, 1, 0)
	currentTabBtn.Position = UDim2.new(0, 0, 0, 0)
	currentTabBtn.BackgroundColor3 = Color3.fromRGB(70, 150, 255)
	currentTabBtn.Text = "📋 Current Character"
	currentTabBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
	currentTabBtn.TextSize = 18
	currentTabBtn.Font = Enum.Font.GothamBold
	currentTabBtn.BorderSizePixel = 0
	currentTabBtn.Parent = tabContainer

	local currentTabCorner = Instance.new("UICorner")
	currentTabCorner.CornerRadius = UDim.new(0, 10)
	currentTabCorner.Parent = currentTabBtn

	-- Past Tab Button
	local pastTabBtn = Instance.new("TextButton")
	pastTabBtn.Name = "PastTab"
	pastTabBtn.Size = UDim2.new(0.5, -5, 1, 0)
	pastTabBtn.Position = UDim2.new(0.5, 5, 0, 0)
	pastTabBtn.BackgroundColor3 = Color3.fromRGB(50, 50, 70)
	pastTabBtn.Text = "📜 Past Characters"
	pastTabBtn.TextColor3 = Color3.fromRGB(200, 200, 200)
	pastTabBtn.TextSize = 18
	pastTabBtn.Font = Enum.Font.Gotham
	pastTabBtn.BorderSizePixel = 0
	pastTabBtn.Parent = tabContainer

	local pastTabCorner = Instance.new("UICorner")
	pastTabCorner.CornerRadius = UDim.new(0, 10)
	pastTabCorner.Parent = pastTabBtn

	-- Content Container
	local contentContainer = Instance.new("Frame")
	contentContainer.Name = "ContentContainer"
	contentContainer.Size = UDim2.new(1, -40, 1, -170)
	contentContainer.Position = UDim2.new(0, 20, 0, 150)
	contentContainer.BackgroundTransparency = 1
	contentContainer.ClipsDescendants = true
	contentContainer.Parent = mainFrame

	-- Current Content Frame
	local currentContent = Instance.new("Frame")
	currentContent.Name = "CurrentContent"
	currentContent.Size = UDim2.new(1, 0, 1, 0)
	currentContent.BackgroundTransparency = 1
	currentContent.Visible = true
	currentContent.Parent = contentContainer

	-- Past Content Frame
	local pastContent = Instance.new("ScrollingFrame")
	pastContent.Name = "PastContent"
	pastContent.Size = UDim2.new(1, 0, 1, 0)
	pastContent.BackgroundTransparency = 1
	pastContent.BorderSizePixel = 0
	pastContent.ScrollBarThickness = 8
	pastContent.ScrollBarImageColor3 = Color3.fromRGB(70, 150, 255)
	pastContent.Visible = false
	pastContent.Parent = contentContainer

	local pastContentList = Instance.new("UIListLayout")
	pastContentList.Padding = UDim.new(0, 15)
	pastContentList.SortOrder = Enum.SortOrder.LayoutOrder
	pastContentList.Parent = pastContent

	-- Tab Switching
	local function switchTab(tab)
		currentTab = tab

		if tab == "current" then
			currentTabBtn.BackgroundColor3 = Color3.fromRGB(70, 150, 255)
			currentTabBtn.Font = Enum.Font.GothamBold
			currentTabBtn.TextColor3 = Color3.fromRGB(255, 255, 255)

			pastTabBtn.BackgroundColor3 = Color3.fromRGB(50, 50, 70)
			pastTabBtn.Font = Enum.Font.Gotham
			pastTabBtn.TextColor3 = Color3.fromRGB(200, 200, 200)

			currentContent.Visible = true
			pastContent.Visible = false
		else
			pastTabBtn.BackgroundColor3 = Color3.fromRGB(70, 150, 255)
			pastTabBtn.Font = Enum.Font.GothamBold
			pastTabBtn.TextColor3 = Color3.fromRGB(255, 255, 255)

			currentTabBtn.BackgroundColor3 = Color3.fromRGB(50, 50, 70)
			currentTabBtn.Font = Enum.Font.Gotham
			currentTabBtn.TextColor3 = Color3.fromRGB(200, 200, 200)

			currentContent.Visible = false
			pastContent.Visible = true
		end
	end

	currentTabBtn.MouseButton1Click:Connect(function() switchTab("current") end)
	pastTabBtn.MouseButton1Click:Connect(function() switchTab("past") end)

	return mainFrame, currentContent, pastContent
end

-- // Create Character Display
local function displayCurrentCharacter(character, container)
	-- Clear existing content
	for _, child in pairs(container:GetChildren()) do
		child:Destroy()
	end

	if not character then
		-- No character - show create button
		local noCharFrame = Instance.new("Frame")
		noCharFrame.Size = UDim2.new(1, 0, 1, 0)
		noCharFrame.BackgroundTransparency = 1
		noCharFrame.Parent = container

		local icon = Instance.new("TextLabel")
		icon.Size = UDim2.new(0, 100, 0, 100)
		icon.Position = UDim2.new(0.5, 0, 0.3, 0)
		icon.AnchorPoint = Vector2.new(0.5, 0.5)
		icon.BackgroundTransparency = 1
		icon.Text = "👤"
		icon.TextSize = 80
		icon.Parent = noCharFrame

		local noCharLabel = Instance.new("TextLabel")
		noCharLabel.Size = UDim2.new(0, 400, 0, 40)
		noCharLabel.Position = UDim2.new(0.5, 0, 0.5, 0)
		noCharLabel.AnchorPoint = Vector2.new(0.5, 0.5)
		noCharLabel.BackgroundTransparency = 1
		noCharLabel.Text = "No Active Character"
		noCharLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
		noCharLabel.TextSize = 24
		noCharLabel.Font = Enum.Font.GothamBold
		noCharLabel.Parent = noCharFrame

		local createBtn = Instance.new("TextButton")
		createBtn.Size = UDim2.new(0, 250, 0, 60)
		createBtn.Position = UDim2.new(0.5, 0, 0.65, 0)
		createBtn.AnchorPoint = Vector2.new(0.5, 0.5)
		createBtn.BackgroundColor3 = Color3.fromRGB(70, 150, 255)
		createBtn.Text = "✨ Create Character"
		createBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
		createBtn.TextSize = 20
		createBtn.Font = Enum.Font.GothamBold
		createBtn.BorderSizePixel = 0
		createBtn.Parent = noCharFrame

		local createBtnCorner = Instance.new("UICorner")
		createBtnCorner.CornerRadius = UDim.new(0, 12)
		createBtnCorner.Parent = createBtn

		animateButton(createBtn)

		createBtn.MouseButton1Click:Connect(function()
			showCreateCharacterForm(container)
		end)
	else
		-- Display character
		local charFrame = Instance.new("Frame")
		charFrame.Size = UDim2.new(1, 0, 1, 0)
		charFrame.BackgroundColor3 = Color3.fromRGB(35, 35, 50)
		charFrame.BorderSizePixel = 0
		charFrame.Parent = container

		local charCorner = Instance.new("UICorner")
		charCorner.CornerRadius = UDim.new(0, 12)
		charCorner.Parent = charFrame

		local padding = Instance.new("UIPadding")
		padding.PaddingLeft = UDim.new(0, 20)
		padding.PaddingRight = UDim.new(0, 20)
		padding.PaddingTop = UDim.new(0, 20)
		padding.PaddingBottom = UDim.new(0, 20)
		padding.Parent = charFrame

		-- Name
		local nameLabel = Instance.new("TextLabel")
		nameLabel.Size = UDim2.new(1, 0, 0, 40)
		nameLabel.BackgroundTransparency = 1
		nameLabel.Text = "👤 " .. character.Name
		nameLabel.TextColor3 = Color3.fromRGB(70, 150, 255)
		nameLabel.TextSize = 28
		nameLabel.Font = Enum.Font.GothamBold
		nameLabel.TextXAlignment = Enum.TextXAlignment.Left
		nameLabel.Parent = charFrame

		-- Birthday
		local birthdayLabel = Instance.new("TextLabel")
		birthdayLabel.Size = UDim2.new(1, 0, 0, 30)
		birthdayLabel.Position = UDim2.new(0, 0, 0, 50)
		birthdayLabel.BackgroundTransparency = 1
		birthdayLabel.Text = "🎂 Born: " .. character.Birthday
		birthdayLabel.TextColor3 = Color3.fromRGB(200, 200, 200)
		birthdayLabel.TextSize = 18
		birthdayLabel.Font = Enum.Font.Gotham
		birthdayLabel.TextXAlignment = Enum.TextXAlignment.Left
		birthdayLabel.Parent = charFrame

		-- Backstory Label
		local backstoryLabel = Instance.new("TextLabel")
		backstoryLabel.Size = UDim2.new(1, 0, 0, 30)
		backstoryLabel.Position = UDim2.new(0, 0, 0, 90)
		backstoryLabel.BackgroundTransparency = 1
		backstoryLabel.Text = "📖 Backstory:"
		backstoryLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
		backstoryLabel.TextSize = 20
		backstoryLabel.Font = Enum.Font.GothamBold
		backstoryLabel.TextXAlignment = Enum.TextXAlignment.Left
		backstoryLabel.Parent = charFrame

		-- Backstory Text
		local backstoryScroll = Instance.new("ScrollingFrame")
		backstoryScroll.Size = UDim2.new(1, 0, 1, -140)
		backstoryScroll.Position = UDim2.new(0, 0, 0, 130)
		backstoryScroll.BackgroundColor3 = Color3.fromRGB(25, 25, 35)
		backstoryScroll.BorderSizePixel = 0
		backstoryScroll.ScrollBarThickness = 6
		backstoryScroll.ScrollBarImageColor3 = Color3.fromRGB(70, 150, 255)
		backstoryScroll.Parent = charFrame

		local backstoryCorner = Instance.new("UICorner")
		backstoryCorner.CornerRadius = UDim.new(0, 8)
		backstoryCorner.Parent = backstoryScroll

		local backstoryText = Instance.new("TextLabel")
		backstoryText.Size = UDim2.new(1, -20, 1, 0)
		backstoryText.Position = UDim2.new(0, 10, 0, 10)
		backstoryText.BackgroundTransparency = 1
		backstoryText.Text = character.Backstory
		backstoryText.TextColor3 = Color3.fromRGB(220, 220, 220)
		backstoryText.TextSize = 16
		backstoryText.Font = Enum.Font.Gotham
		backstoryText.TextWrapped = true
		backstoryText.TextXAlignment = Enum.TextXAlignment.Left
		backstoryText.TextYAlignment = Enum.TextYAlignment.Top
		backstoryText.Parent = backstoryScroll

		backstoryScroll.CanvasSize = UDim2.new(0, 0, 0, backstoryText.TextBounds.Y + 20)
	end
end

-- // Display Past Characters
local function displayPastCharacters(characters, container)
	-- Clear existing
	for _, child in pairs(container:GetChildren()) do
		if child:IsA("Frame") then
			child:Destroy()
		end
	end

	if #characters == 0 then
		local noCharsFrame = Instance.new("Frame")
		noCharsFrame.Size = UDim2.new(1, 0, 0, 200)
		noCharsFrame.BackgroundTransparency = 1
		noCharsFrame.Parent = container

		local icon = Instance.new("TextLabel")
		icon.Size = UDim2.new(1, 0, 0, 80)
		icon.Position = UDim2.new(0, 0, 0, 40)
		icon.BackgroundTransparency = 1
		icon.Text = "📜"
		icon.TextSize = 60
		icon.Parent = noCharsFrame

		local label = Instance.new("TextLabel")
		label.Size = UDim2.new(1, 0, 0, 40)
		label.Position = UDim2.new(0, 0, 0, 130)
		label.BackgroundTransparency = 1
		label.Text = "No Past Characters"
		label.TextColor3 = Color3.fromRGB(150, 150, 150)
		label.TextSize = 20
		label.Font = Enum.Font.Gotham
		label.Parent = noCharsFrame

		container.CanvasSize = UDim2.new(0, 0, 0, 200)
	else
		for i, char in ipairs(characters) do
			local charCard = Instance.new("Frame")
			charCard.Size = UDim2.new(1, 0, 0, 150)
			charCard.BackgroundColor3 = Color3.fromRGB(35, 35, 50)
			charCard.BorderSizePixel = 0
			charCard.LayoutOrder = i
			charCard.Parent = container

			local cardCorner = Instance.new("UICorner")
			cardCorner.CornerRadius = UDim.new(0, 12)
			cardCorner.Parent = charCard

			local cardPadding = Instance.new("UIPadding")
			cardPadding.PaddingLeft = UDim.new(0, 15)
			cardPadding.PaddingRight = UDim.new(0, 15)
			cardPadding.PaddingTop = UDim.new(0, 15)
			cardPadding.PaddingBottom = UDim.new(0, 15)
			cardPadding.Parent = charCard

			-- Status indicator
			local statusIndicator = Instance.new("Frame")
			statusIndicator.Size = UDim2.new(0, 8, 1, -30)
			statusIndicator.Position = UDim2.new(0, -15, 0, 15)
			statusIndicator.BackgroundColor3 = Color3.fromRGB(255, 70, 70)
			statusIndicator.BorderSizePixel = 0
			statusIndicator.Parent = charCard

			-- Name
			local nameLabel = Instance.new("TextLabel")
			nameLabel.Size = UDim2.new(1, -100, 0, 30)
			nameLabel.BackgroundTransparency = 1
			nameLabel.Text = "☠️ " .. char.Name
			nameLabel.TextColor3 = Color3.fromRGB(255, 100, 100)
			nameLabel.TextSize = 22
			nameLabel.Font = Enum.Font.GothamBold
			nameLabel.TextXAlignment = Enum.TextXAlignment.Left
			nameLabel.Parent = charCard

			-- Dates
			local datesLabel = Instance.new("TextLabel")
			datesLabel.Size = UDim2.new(1, -100, 0, 25)
			datesLabel.Position = UDim2.new(0, 0, 0, 35)
			datesLabel.BackgroundTransparency = 1
			datesLabel.Text = string.format("🎂 %s  -  ☠️ %s", char.Birthday, char.DeathDate or "Unknown")
			datesLabel.TextColor3 = Color3.fromRGB(180, 180, 180)
			datesLabel.TextSize = 14
			datesLabel.Font = Enum.Font.Gotham
			datesLabel.TextXAlignment = Enum.TextXAlignment.Left
			datesLabel.Parent = charCard

			-- Backstory preview
			local backstoryPreview = Instance.new("TextLabel")
			backstoryPreview.Size = UDim2.new(1, -100, 0, 60)
			backstoryPreview.Position = UDim2.new(0, 0, 0, 65)
			backstoryPreview.BackgroundTransparency = 1
			backstoryPreview.Text = string.sub(char.Backstory, 1, 120) .. (string.len(char.Backstory) > 120 and "..." or "")
			backstoryPreview.TextColor3 = Color3.fromRGB(150, 150, 150)
			backstoryPreview.TextSize = 14
			backstoryPreview.Font = Enum.Font.Gotham
			backstoryPreview.TextWrapped = true
			backstoryPreview.TextXAlignment = Enum.TextXAlignment.Left
			backstoryPreview.TextYAlignment = Enum.TextYAlignment.Top
			backstoryPreview.Parent = charCard
		end

		container.CanvasSize = UDim2.new(0, 0, 0, (#characters * 165))
	end
end

-- // Create Character Form
function showCreateCharacterForm(container)
	-- Clear container
	for _, child in pairs(container:GetChildren()) do
		child:Destroy()
	end

	local formFrame = Instance.new("ScrollingFrame")
	formFrame.Size = UDim2.new(1, 0, 1, 0)
	formFrame.BackgroundColor3 = Color3.fromRGB(35, 35, 50)
	formFrame.BorderSizePixel = 0
	formFrame.ScrollBarThickness = 8
	formFrame.ScrollBarImageColor3 = Color3.fromRGB(70, 150, 255)
	formFrame.CanvasSize = UDim2.new(0, 0, 0, 550)
	formFrame.Parent = container

	local formCorner = Instance.new("UICorner")
	formCorner.CornerRadius = UDim.new(0, 12)
	formCorner.Parent = formFrame

	local formPadding = Instance.new("UIPadding")
	formPadding.PaddingLeft = UDim.new(0, 30)
	formPadding.PaddingRight = UDim.new(0, 30)
	formPadding.PaddingTop = UDim.new(0, 30)
	formPadding.PaddingBottom = UDim.new(0, 30)
	formPadding.Parent = formFrame

	-- Title
	local formTitle = Instance.new("TextLabel")
	formTitle.Size = UDim2.new(1, 0, 0, 40)
	formTitle.BackgroundTransparency = 1
	formTitle.Text = "✨ Create Your Character"
	formTitle.TextColor3 = Color3.fromRGB(70, 150, 255)
	formTitle.TextSize = 26
	formTitle.Font = Enum.Font.GothamBold
	formTitle.TextXAlignment = Enum.TextXAlignment.Left
	formTitle.Parent = formFrame

	local formSubtitle = Instance.new("TextLabel")
	formSubtitle.Size = UDim2.new(1, 0, 0, 30)
	formSubtitle.Position = UDim2.new(0, 0, 0, 45)
	formSubtitle.BackgroundTransparency = 1
	formSubtitle.Text = "⚠️ Once created, your character cannot be edited or deleted unless you die in a permadeath event."
	formSubtitle.TextColor3 = Color3.fromRGB(255, 200, 100)
	formSubtitle.TextSize = 13
	formSubtitle.Font = Enum.Font.Gotham
	formSubtitle.TextWrapped = true
	formSubtitle.TextXAlignment = Enum.TextXAlignment.Left
	formSubtitle.Parent = formFrame

	-- Name Label
	local nameLabel = Instance.new("TextLabel")
	nameLabel.Size = UDim2.new(1, 0, 0, 25)
	nameLabel.Position = UDim2.new(0, 0, 0, 100)
	nameLabel.BackgroundTransparency = 1
	nameLabel.Text = "Character Name *"
	nameLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	nameLabel.TextSize = 16
	nameLabel.Font = Enum.Font.GothamBold
	nameLabel.TextXAlignment = Enum.TextXAlignment.Left
	nameLabel.Parent = formFrame

	-- Name Input
	local nameInput = Instance.new("TextBox")
	nameInput.Size = UDim2.new(1, 0, 0, 45)
	nameInput.Position = UDim2.new(0, 0, 0, 130)
	nameInput.BackgroundColor3 = Color3.fromRGB(25, 25, 35)
	nameInput.BorderSizePixel = 0
	nameInput.Text = ""
	nameInput.PlaceholderText = "Enter character name..."
	nameInput.TextColor3 = Color3.fromRGB(255, 255, 255)
	nameInput.PlaceholderColor3 = Color3.fromRGB(120, 120, 120)
	nameInput.TextSize = 16
	nameInput.Font = Enum.Font.Gotham
	nameInput.TextXAlignment = Enum.TextXAlignment.Left
	nameInput.ClearTextOnFocus = false
	nameInput.Parent = formFrame

	local nameCorner = Instance.new("UICorner")
	nameCorner.CornerRadius = UDim.new(0, 8)
	nameCorner.Parent = nameInput

	local namePadding = Instance.new("UIPadding")
	namePadding.PaddingLeft = UDim.new(0, 15)
	namePadding.PaddingRight = UDim.new(0, 15)
	namePadding.Parent = nameInput

	-- Birthday Label (Auto-filled)
	local birthdayLabel = Instance.new("TextLabel")
	birthdayLabel.Size = UDim2.new(1, 0, 0, 25)
	birthdayLabel.Position = UDim2.new(0, 0, 0, 195)
	birthdayLabel.BackgroundTransparency = 1
	birthdayLabel.Text = "Birthday (Auto-filled)"
	birthdayLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	birthdayLabel.TextSize = 16
	birthdayLabel.Font = Enum.Font.GothamBold
	birthdayLabel.TextXAlignment = Enum.TextXAlignment.Left
	birthdayLabel.Parent = formFrame

	local birthdayDisplay = Instance.new("TextLabel")
	birthdayDisplay.Size = UDim2.new(1, 0, 0, 45)
	birthdayDisplay.Position = UDim2.new(0, 0, 0, 225)
	birthdayDisplay.BackgroundColor3 = Color3.fromRGB(25, 25, 35)
	birthdayDisplay.BorderSizePixel = 0
	birthdayDisplay.Text = "🎂 " .. os.date("%B %d, %Y")
	birthdayDisplay.TextColor3 = Color3.fromRGB(70, 150, 255)
	birthdayDisplay.TextSize = 16
	birthdayDisplay.Font = Enum.Font.GothamBold
	birthdayDisplay.Parent = formFrame

	local birthdayCorner = Instance.new("UICorner")
	birthdayCorner.CornerRadius = UDim.new(0, 8)
	birthdayCorner.Parent = birthdayDisplay

	-- Backstory Label
	local backstoryLabel = Instance.new("TextLabel")
	backstoryLabel.Size = UDim2.new(1, 0, 0, 25)
	backstoryLabel.Position = UDim2.new(0, 0, 0, 290)
	backstoryLabel.BackgroundTransparency = 1
	backstoryLabel.Text = "Character Backstory *"
	backstoryLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
	backstoryLabel.TextSize = 16
	backstoryLabel.Font = Enum.Font.GothamBold
	backstoryLabel.TextXAlignment = Enum.TextXAlignment.Left
	backstoryLabel.Parent = formFrame

	-- Backstory Input
	local backstoryInput = Instance.new("TextBox")
	backstoryInput.Size = UDim2.new(1, 0, 0, 120)
	backstoryInput.Position = UDim2.new(0, 0, 0, 320)
	backstoryInput.BackgroundColor3 = Color3.fromRGB(25, 25, 35)
	backstoryInput.BorderSizePixel = 0
	backstoryInput.Text = ""
	backstoryInput.PlaceholderText = "Write your character's backstory... Who are they? Where did they come from?"
	backstoryInput.TextColor3 = Color3.fromRGB(255, 255, 255)
	backstoryInput.PlaceholderColor3 = Color3.fromRGB(120, 120, 120)
	backstoryInput.TextSize = 15
	backstoryInput.Font = Enum.Font.Gotham
	backstoryInput.TextXAlignment = Enum.TextXAlignment.Left
	backstoryInput.TextYAlignment = Enum.TextYAlignment.Top
	backstoryInput.TextWrapped = true
	backstoryInput.MultiLine = true
	backstoryInput.ClearTextOnFocus = false
	backstoryInput.Parent = formFrame

	local backstoryCorner = Instance.new("UICorner")
	backstoryCorner.CornerRadius = UDim.new(0, 8)
	backstoryCorner.Parent = backstoryInput

	local backstoryPadding = Instance.new("UIPadding")
	backstoryPadding.PaddingLeft = UDim.new(0, 15)
	backstoryPadding.PaddingRight = UDim.new(0, 15)
	backstoryPadding.PaddingTop = UDim.new(0, 10)
	backstoryPadding.PaddingBottom = UDim.new(0, 10)
	backstoryPadding.Parent = backstoryInput

	-- Buttons Container
	local btnContainer = Instance.new("Frame")
	btnContainer.Size = UDim2.new(1, 0, 0, 60)
	btnContainer.Position = UDim2.new(0, 0, 0, 460)
	btnContainer.BackgroundTransparency = 1
	btnContainer.Parent = formFrame

	-- Cancel Button
	local cancelBtn = Instance.new("TextButton")
	cancelBtn.Size = UDim2.new(0.48, 0, 1, 0)
	cancelBtn.Position = UDim2.new(0, 0, 0, 0)
	cancelBtn.BackgroundColor3 = Color3.fromRGB(80, 80, 90)
	cancelBtn.Text = "Cancel"
	cancelBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
	cancelBtn.TextSize = 18
	cancelBtn.Font = Enum.Font.GothamBold
	cancelBtn.BorderSizePixel = 0
	cancelBtn.Parent = btnContainer

	local cancelCorner = Instance.new("UICorner")
	cancelCorner.CornerRadius = UDim.new(0, 10)
	cancelCorner.Parent = cancelBtn

	-- Submit Button
	local submitBtn = Instance.new("TextButton")
	submitBtn.Size = UDim2.new(0.48, 0, 1, 0)
	submitBtn.Position = UDim2.new(0.52, 0, 0, 0)
	submitBtn.BackgroundColor3 = Color3.fromRGB(70, 200, 100)
	submitBtn.Text = "✨ Create Character"
	submitBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
	submitBtn.TextSize = 18
	submitBtn.Font = Enum.Font.GothamBold
	submitBtn.BorderSizePixel = 0
	submitBtn.Parent = btnContainer

	local submitCorner = Instance.new("UICorner")
	submitCorner.CornerRadius = UDim.new(0, 10)
	submitCorner.Parent = submitBtn

	animateButton(cancelBtn)
	animateButton(submitBtn)

	-- Cancel action
	cancelBtn.MouseButton1Click:Connect(function()
		GetCharacterData:FireServer()
	end)

	-- Submit action
	submitBtn.MouseButton1Click:Connect(function()
		local name = nameInput.Text
		local backstory = backstoryInput.Text

		if name == "" or backstory == "" then
			-- Show error
			submitBtn.BackgroundColor3 = Color3.fromRGB(255, 70, 70)
			submitBtn.Text = "❌ Fill All Fields!"
			wait(2)
			submitBtn.BackgroundColor3 = Color3.fromRGB(70, 200, 100)
			submitBtn.Text = "✨ Create Character"
			return
		end

		if string.len(name) < 2 then
			submitBtn.BackgroundColor3 = Color3.fromRGB(255, 70, 70)
			submitBtn.Text = "❌ Name Too Short!"
			wait(2)
			submitBtn.BackgroundColor3 = Color3.fromRGB(70, 200, 100)
			submitBtn.Text = "✨ Create Character"
			return
		end

		if string.len(backstory) < 20 then
			submitBtn.BackgroundColor3 = Color3.fromRGB(255, 70, 70)
			submitBtn.Text = "❌ Backstory Too Short!"
			wait(2)
			submitBtn.BackgroundColor3 = Color3.fromRGB(70, 200, 100)
			submitBtn.Text = "✨ Create Character"
			return
		end

		-- Send to server
		submitBtn.Text = "⏳ Creating..."
		CreateCharacter:FireServer({
			Name = name,
			Backstory = backstory
		})
	end)
end

-- // Open UI Handler
OpenCharacterUI.OnClientEvent:Connect(function(data)
	print("[Character Client] Received data from server")
	currentData = data

	local mainFrame, currentContent, pastContent = createMainUI()

	-- Display current character
	displayCurrentCharacter(data.currentCharacter, currentContent)

	-- Display past characters
	displayPastCharacters(data.pastCharacters or {}, pastContent)

	-- Show UI with animation
	mainFrame.Visible = true
	mainFrame.Size = UDim2.new(0, 0, 0, 0)
	createTween(mainFrame, {Size = UDim2.new(0, 800, 0, 600)}):Play()
end)

-- // Command to open UI
local function setupCommand()
	player.Chatted:Connect(function(message)
		if message:lower() == "/character" or message:lower() == "/char" then
			GetCharacterData:FireServer()
		end
	end)
end

setupCommand()

print("[Character Client] ✅ Client script loaded! Type /character or /char to open UI")

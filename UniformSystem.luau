local GroupService = game:GetService("GroupService")
local Players = game:GetService("Players")

local GROUP_ID = 0000000

local UNIFORMS = {
	Enlisted = {
		[1] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
		},
		[2] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
		},
		[3] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
		},
		[4] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
		},
		[5] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
			{Name = "Special Ops", ShirtID = 0, PantsID = 0},
		},
		[6] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
			{Name = "Special Ops", ShirtID = 0, PantsID = 0},
		},
		[7] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
			{Name = "Special Ops", ShirtID = 0, PantsID = 0},
		},
		[8] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
			{Name = "Special Ops", ShirtID = 0, PantsID = 0},
		},
		[9] = {
			{Name = "Woodland Camo", ShirtID = 0, PantsID = 0},
			{Name = "Desert Camo", ShirtID = 0, PantsID = 0},
			{Name = "Urban Camo", ShirtID = 0, PantsID = 0},
			{Name = "Special Ops", ShirtID = 0, PantsID = 0},
			{Name = "Command Black", ShirtID = 0, PantsID = 0},
		},
	},
	Formal = {
		[1] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
		},
		[2] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
		},
		[3] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
		},
		[4] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
			{Name = "Service Dress", ShirtID = 0, PantsID = 0},
		},
		[5] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
			{Name = "Service Dress", ShirtID = 0, PantsID = 0},
		},
		[6] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
			{Name = "Service Dress", ShirtID = 0, PantsID = 0},
		},
		[7] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
			{Name = "Service Dress", ShirtID = 0, PantsID = 0},
			{Name = "Mess Dress", ShirtID = 0, PantsID = 0},
		},
		[8] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
			{Name = "Service Dress", ShirtID = 0, PantsID = 0},
			{Name = "Mess Dress", ShirtID = 0, PantsID = 0},
		},
		[9] = {
			{Name = "Class A", ShirtID = 0, PantsID = 0},
			{Name = "Class B", ShirtID = 0, PantsID = 0},
			{Name = "Service Dress", ShirtID = 0, PantsID = 0},
			{Name = "Mess Dress", ShirtID = 0, PantsID = 0},
			{Name = "Ceremonial", ShirtID = 0, PantsID = 0},
		},
	}
}

local function createGUI(player)
	local playerGui = player:WaitForChild("PlayerGui")
	
	if playerGui:FindFirstChild("UniformSystem") then
		playerGui.UniformSystem:Destroy()
	end
	
	local screenGui = Instance.new("ScreenGui")
	screenGui.Name = "UniformSystem"
	screenGui.ResetOnSpawn = false
	screenGui.Parent = playerGui
	
	local openButton = Instance.new("TextButton")
	openButton.Name = "OpenButton"
	openButton.Size = UDim2.new(0, 120, 0, 50)
	openButton.Position = UDim2.new(0, 20, 0.5, -25)
	openButton.BackgroundColor3 = Color3.fromRGB(50, 150, 50)
	openButton.Text = "UNIFORMS"
	openButton.TextColor3 = Color3.new(1, 1, 1)
	openButton.TextSize = 18
	openButton.Font = Enum.Font.GothamBold
	openButton.Parent = screenGui
	
	local openBtnCorner = Instance.new("UICorner")
	openBtnCorner.CornerRadius = UDim.new(0, 10)
	openBtnCorner.Parent = openButton
	
	local mainFrame = Instance.new("Frame")
	mainFrame.Name = "MainFrame"
	mainFrame.Size = UDim2.new(0, 700, 0, 500)
	mainFrame.Position = UDim2.new(0.5, -350, 0.5, -250)
	mainFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
	mainFrame.BorderSizePixel = 0
	mainFrame.Visible = false
	mainFrame.Parent = screenGui
	
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 12)
	corner.Parent = mainFrame
	
	local title = Instance.new("TextLabel")
	title.Size = UDim2.new(1, 0, 0, 50)
	title.BackgroundColor3 = Color3.fromRGB(20, 20, 30)
	title.Text = "MILITARY UNIFORM SYSTEM"
	title.TextColor3 = Color3.new(1, 1, 1)
	title.TextSize = 20
	title.Font = Enum.Font.GothamBold
	title.Parent = mainFrame
	
	local titleCorner = Instance.new("UICorner")
	titleCorner.CornerRadius = UDim.new(0, 12)
	titleCorner.Parent = title
	
	local closeBtn = Instance.new("TextButton")
	closeBtn.Size = UDim2.new(0, 40, 0, 40)
	closeBtn.Position = UDim2.new(1, -45, 0, 5)
	closeBtn.BackgroundColor3 = Color3.fromRGB(200, 50, 50)
	closeBtn.Text = "X"
	closeBtn.TextColor3 = Color3.new(1, 1, 1)
	closeBtn.TextSize = 18
	closeBtn.Font = Enum.Font.GothamBold
	closeBtn.Parent = mainFrame
	
	local closeBtnCorner = Instance.new("UICorner")
	closeBtnCorner.CornerRadius = UDim.new(0, 8)
	closeBtnCorner.Parent = closeBtn
	
	openButton.MouseButton1Click:Connect(function()
		mainFrame.Visible = not mainFrame.Visible
	end)
	
	closeBtn.MouseButton1Click:Connect(function()
		mainFrame.Visible = false
	end)
	
	local rankLabel = Instance.new("TextLabel")
	rankLabel.Size = UDim2.new(1, -20, 0, 30)
	rankLabel.Position = UDim2.new(0, 10, 0, 60)
	rankLabel.BackgroundTransparency = 1
	rankLabel.Text = "Current Rank: Loading..."
	rankLabel.TextColor3 = Color3.fromRGB(100, 200, 255)
	rankLabel.TextSize = 16
	rankLabel.Font = Enum.Font.GothamBold
	rankLabel.TextXAlignment = Enum.TextXAlignment.Left
	rankLabel.Parent = mainFrame
	
	local enlistedLabel = Instance.new("TextLabel")
	enlistedLabel.Size = UDim2.new(0.5, -15, 0, 25)
	enlistedLabel.Position = UDim2.new(0, 10, 0, 100)
	enlistedLabel.BackgroundTransparency = 1
	enlistedLabel.Text = "ENLISTED UNIFORMS"
	enlistedLabel.TextColor3 = Color3.fromRGB(150, 255, 150)
	enlistedLabel.TextSize = 14
	enlistedLabel.Font = Enum.Font.GothamBold
	enlistedLabel.TextXAlignment = Enum.TextXAlignment.Left
	enlistedLabel.Parent = mainFrame
	
	local enlistedScroll = Instance.new("ScrollingFrame")
	enlistedScroll.Size = UDim2.new(0.5, -15, 0, 360)
	enlistedScroll.Position = UDim2.new(0, 10, 0, 130)
	enlistedScroll.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
	enlistedScroll.BorderSizePixel = 0
	enlistedScroll.ScrollBarThickness = 6
	enlistedScroll.Parent = mainFrame
	
	local enlistedCorner = Instance.new("UICorner")
	enlistedCorner.CornerRadius = UDim.new(0, 8)
	enlistedCorner.Parent = enlistedScroll
	
	local enlistedLayout = Instance.new("UIListLayout")
	enlistedLayout.Padding = UDim.new(0, 8)
	enlistedLayout.Parent = enlistedScroll
	
	local formalLabel = Instance.new("TextLabel")
	formalLabel.Size = UDim2.new(0.5, -15, 0, 25)
	formalLabel.Position = UDim2.new(0.5, 5, 0, 100)
	formalLabel.BackgroundTransparency = 1
	formalLabel.Text = "FORMAL UNIFORMS"
	formalLabel.TextColor3 = Color3.fromRGB(255, 200, 100)
	formalLabel.TextSize = 14
	formalLabel.Font = Enum.Font.GothamBold
	formalLabel.TextXAlignment = Enum.TextXAlignment.Left
	formalLabel.Parent = mainFrame
	
	local formalScroll = Instance.new("ScrollingFrame")
	formalScroll.Size = UDim2.new(0.5, -15, 0, 360)
	formalScroll.Position = UDim2.new(0.5, 5, 0, 130)
	formalScroll.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
	formalScroll.BorderSizePixel = 0
	formalScroll.ScrollBarThickness = 6
	formalScroll.Parent = mainFrame
	
	local formalCorner = Instance.new("UICorner")
	formalCorner.CornerRadius = UDim.new(0, 8)
	formalCorner.Parent = formalScroll
	
	local formalLayout = Instance.new("UIListLayout")
	formalLayout.Padding = UDim.new(0, 8)
	formalLayout.Parent = formalScroll
	
	return screenGui, enlistedScroll, formalScroll, rankLabel
end

local function getPlayerRank(player)
	local success, rank = pcall(function()
		return player:GetRankInGroup(GROUP_ID)
	end)
	if success then
		return rank
	end
	return 0
end

local function applyUniform(player, uniform)
	local character = player.Character
	if not character then return end
	
	for _, item in pairs(character:GetChildren()) do
		if item:IsA("Shirt") or item:IsA("Pants") then
			item:Destroy()
		end
	end
	
	if uniform.ShirtID ~= 0 then
		local shirt = Instance.new("Shirt")
		shirt.ShirtTemplate = "rbxassetid://" .. uniform.ShirtID
		shirt.Parent = character
	end
	
	if uniform.PantsID ~= 0 then
		local pants = Instance.new("Pants")
		pants.PantsTemplate = "rbxassetid://" .. uniform.PantsID
		pants.Parent = character
	end
end

local function createRankHeader(parent, rankNum)
	local header = Instance.new("Frame")
	header.Size = UDim2.new(1, -10, 0, 30)
	header.BackgroundColor3 = Color3.fromRGB(60, 60, 75)
	header.BorderSizePixel = 0
	header.Parent = parent
	
	local headerCorner = Instance.new("UICorner")
	headerCorner.CornerRadius = UDim.new(0, 6)
	headerCorner.Parent = header
	
	local label = Instance.new("TextLabel")
	label.Size = UDim2.new(1, -10, 1, 0)
	label.Position = UDim2.new(0, 10, 0, 0)
	label.BackgroundTransparency = 1
	label.Text = "E-" .. rankNum
	label.TextColor3 = Color3.fromRGB(255, 220, 100)
	label.TextSize = 14
	label.Font = Enum.Font.GothamBold
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.Parent = header
	
	return header
end

local function createUniformButton(parent, uniform, player)
	local button = Instance.new("TextButton")
	button.Size = UDim2.new(1, -20, 0, 45)
	button.BackgroundColor3 = Color3.fromRGB(50, 50, 65)
	button.Text = ""
	button.AutoButtonColor = true
	button.Parent = parent
	
	local btnCorner = Instance.new("UICorner")
	btnCorner.CornerRadius = UDim.new(0, 6)
	btnCorner.Parent = button
	
	local label = Instance.new("TextLabel")
	label.Size = UDim2.new(1, -60, 1, 0)
	label.Position = UDim2.new(0, 10, 0, 0)
	label.BackgroundTransparency = 1
	label.Text = uniform.Name
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextSize = 13
	label.Font = Enum.Font.Gotham
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.Parent = button
	
	local icon = Instance.new("TextLabel")
	icon.Size = UDim2.new(0, 30, 0, 30)
	icon.Position = UDim2.new(1, -40, 0.5, -15)
	icon.BackgroundTransparency = 1
	icon.Text = "✓"
	icon.TextColor3 = Color3.fromRGB(100, 255, 100)
	icon.TextSize = 16
	icon.Font = Enum.Font.GothamBold
	icon.Parent = button
	
	button.MouseButton1Click:Connect(function()
		applyUniform(player, uniform)
		button.BackgroundColor3 = Color3.fromRGB(70, 100, 70)
		wait(0.2)
		button.BackgroundColor3 = Color3.fromRGB(50, 50, 65)
	end)
	
	return button
end

local function populateUniforms(player, enlistedScroll, formalScroll, playerRank)
	for _, child in pairs(enlistedScroll:GetChildren()) do
		if not child:IsA("UIListLayout") then
			child:Destroy()
		end
	end
	for _, child in pairs(formalScroll:GetChildren()) do
		if not child:IsA("UIListLayout") then
			child:Destroy()
		end
	end
	
	local enlistedHeight = 0
	local formalHeight = 0
	
	for rankNum = 1, playerRank do
		if UNIFORMS.Enlisted[rankNum] and #UNIFORMS.Enlisted[rankNum] > 0 then
			createRankHeader(enlistedScroll, rankNum)
			enlistedHeight = enlistedHeight + 38
			
			for _, uniform in ipairs(UNIFORMS.Enlisted[rankNum]) do
				createUniformButton(enlistedScroll, uniform, player)
				enlistedHeight = enlistedHeight + 53
			end
		end
	end
	
	for rankNum = 1, playerRank do
		if UNIFORMS.Formal[rankNum] and #UNIFORMS.Formal[rankNum] > 0 then
			createRankHeader(formalScroll, rankNum)
			formalHeight = formalHeight + 38
			
			for _, uniform in ipairs(UNIFORMS.Formal[rankNum]) do
				createUniformButton(formalScroll, uniform, player)
				formalHeight = formalHeight + 53
			end
		end
	end
	
	enlistedScroll.CanvasSize = UDim2.new(0, 0, 0, enlistedHeight)
	formalScroll.CanvasSize = UDim2.new(0, 0, 0, formalHeight)
end

local function initializePlayer(player)
	player.CharacterAdded:Wait()
	wait(1)
	
	local playerRank = getPlayerRank(player)
	local gui, enlistedScroll, formalScroll, rankLabel = createGUI(player)
	
	rankLabel.Text = "Current Rank: E-" .. playerRank .. " (Group Rank " .. playerRank .. ")"
	populateUniforms(player, enlistedScroll, formalScroll, playerRank)
end

for _, player in pairs(Players:GetPlayers()) do
	coroutine.wrap(function()
		initializePlayer(player)
	end)()
end

Players.PlayerAdded:Connect(function(player)
	initializePlayer(player)
end)

print("✓ Uniform System Installed Successfully!")

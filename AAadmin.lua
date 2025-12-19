
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local StarterGui = game:GetService("StarterGui")

local player = Players.LocalPlayer

-- CONFIG
local CONFIG = {
	Prefix = ":",
	ConsoleKey = Enum.KeyCode.Quote,
	Theme = {
		Primary = Color3.fromRGB(25, 25, 35),
		Secondary = Color3.fromRGB(35, 35, 45),
		Accent = Color3.fromRGB(88, 101, 242),
		Success = Color3.fromRGB(87, 242, 135),
		Error = Color3.fromRGB(242, 87, 87),
		Warning = Color3.fromRGB(242, 199, 87),
		Text = Color3.fromRGB(255, 255, 255),
		TextDark = Color3.fromRGB(180, 180, 190)
	}
}

-- ADMIN LEVELS
local AdminLevels = {
	[5] = "Owner",
	[4] = "SuperAdmin", 
	[3] = "Admin",
	[2] = "Moderator",
	[1] = "VIP",
	[0] = "Player"
}

local Admins = {
	[8802544916] = 5,
	[467330362] = 5,
}

-- STORAGE
local Commands = {}
local CommandHistory = {}
local ActiveEffects = {}
local GUI

-- FUNCTIONS
local function GetAdminLevel()
	return Admins[player.UserId] or 0
end

local function GetPlayers(name)
	if not name then return {} end
	name = name:lower()
	if name == "me" then return {player}
	elseif name == "all" then return Players:GetPlayers()
	elseif name == "others" then
		local p = {}
		for _, v in ipairs(Players:GetPlayers()) do
			if v ~= player then table.insert(p, v) end
		end
		return p
	else
		for _, v in ipairs(Players:GetPlayers()) do
			if v.Name:lower():find(name) then return {v} end
		end
	end
	return {}
end

-- WORKING NOTIFICATION SYSTEM
local function Notify(text, color)
	spawn(function()
		if not GUI then return end

		local notif = Instance.new("Frame")
		notif.Size = UDim2.new(0, 320, 0, 70)
		notif.Position = UDim2.new(1, -330, 0, 20)
		notif.BackgroundColor3 = color or CONFIG.Theme.Success
		notif.BorderSizePixel = 0
		notif.Parent = GUI

		Instance.new("UICorner", notif).CornerRadius = UDim.new(0, 10)

		local label = Instance.new("TextLabel")
		label.Text = text
		label.Size = UDim2.new(1, -20, 1, -10)
		label.Position = UDim2.new(0, 10, 0, 5)
		label.BackgroundTransparency = 1
		label.Font = Enum.Font.GothamBold
		label.TextSize = 15
		label.TextColor3 = Color3.new(1, 1, 1)
		label.TextWrapped = true
		label.TextXAlignment = Enum.TextXAlignment.Left
		label.TextYAlignment = Enum.TextYAlignment.Center
		label.Parent = notif

		task.delay(2.5, function()
			if notif and notif.Parent then
				notif:Destroy()
			end
		end)
	end)
end

-- FUZZY MATCH
local function FuzzyMatch(str, pattern)
	str, pattern = str:lower(), pattern:lower()
	if str:find(pattern, 1, true) then return true end
	local idx = 1
	for i = 1, #str do
		if str:sub(i,i) == pattern:sub(idx,idx) then
			idx = idx + 1
			if idx > #pattern then return true end
		end
	end
	return false
end

-- REGISTER COMMAND
local function Cmd(name, aliases, desc, level, func)
	local cmd = {Name=name, Aliases=aliases or {}, Desc=desc, Level=level, Func=func}
	Commands[name:lower()] = cmd
	for _, a in ipairs(aliases) do Commands[a:lower()] = cmd end
end

-- ========== ALL COMMANDS ==========
local function RegisterAllCommands()

	-- INFO
	Cmd("cmds", {"commands", "help"}, "Show all commands", 0, function(args)
		Notify("Press '" .. CONFIG.ConsoleKey.Name .. "' to open panel!", CONFIG.Theme.Accent)
	end)

	Cmd("admin", {"level"}, "Your admin level", 0, function(args)
		Notify("Level: " .. AdminLevels[GetAdminLevel()] .. " (" .. GetAdminLevel() .. ")", CONFIG.Theme.Success)
	end)

	Cmd("admins", {}, "List admins", 0, function(args)
		local list = {}
		for _, p in ipairs(Players:GetPlayers()) do
			local lvl = Admins[p.UserId] or 0
			if lvl > 0 then table.insert(list, p.Name .. " (" .. AdminLevels[lvl] .. ")") end
		end
		Notify(#list > 0 and "Admins: " .. table.concat(list, ", ") or "No admins online", CONFIG.Theme.Success)
	end)

	Cmd("players", {"plrs"}, "List players", 0, function(args)
		local list = {}
		for _, p in ipairs(Players:GetPlayers()) do table.insert(list, p.Name) end
		Notify("Players (" .. #list .. "): " .. table.concat(list, ", "), CONFIG.Theme.Success)
	end)

	-- MOVEMENT
	Cmd("speed", {"ws", "walkspeed"}, "Set speed (:speed 100)", 1, function(args)
		local s = tonumber(args[1]) or 16
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.WalkSpeed = s
			Notify("Speed: " .. s, CONFIG.Theme.Success)
		end
	end)

	Cmd("jump", {"jp", "jumppower"}, "Set jump (:jump 100)", 1, function(args)
		local j = tonumber(args[1]) or 50
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.JumpPower = j
			player.Character.Humanoid.UseJumpPower = true
			Notify("Jump: " .. j, CONFIG.Theme.Success)
		end
	end)

	Cmd("tp", {"teleport", "goto"}, "Teleport to player", 1, function(args)
		local t = GetPlayers(args[1])[1]
		if t and t.Character and t.Character:FindFirstChild("HumanoidRootPart") then
			if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
				player.Character.HumanoidRootPart.CFrame = t.Character.HumanoidRootPart.CFrame
				Notify("Teleported to " .. t.Name, CONFIG.Theme.Success)
			end
		else
			Notify("Player not found", CONFIG.Theme.Error)
		end
	end)

	Cmd("bring", {"summon"}, "Bring player", 2, function(args)
		local t = GetPlayers(args[1])
		if #t > 0 and player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			for _, p in ipairs(t) do
				if p.Character and p.Character:FindFirstChild("HumanoidRootPart") then
					p.Character.HumanoidRootPart.CFrame = player.Character.HumanoidRootPart.CFrame
				end
			end
			Notify("Brought " .. #t .. " player(s)", CONFIG.Theme.Success)
		end
	end)

	-- FLY (IMPROVED)
	Cmd("fly", {}, "Fly (WASD, Space=up, Shift=down)", 1, function(args)
		if ActiveEffects.Fly then
			Notify("Already flying!", CONFIG.Theme.Warning)
			return
		end

		local char = player.Character
		if not char or not char:FindFirstChild("HumanoidRootPart") then return end

		local hrp = char.HumanoidRootPart
		local speed = 50

		local bg = Instance.new("BodyGyro")
		bg.MaxTorque = Vector3.new(9e9, 9e9, 9e9)
		bg.Parent = hrp

		local bv = Instance.new("BodyVelocity")
		bv.MaxForce = Vector3.new(9e9, 9e9, 9e9)
		bv.Parent = hrp

		local ctrl = {f=0,b=0,l=0,r=0,u=0,d=0}

		local function update()
			if not char or not char.Parent then return end
			local cam = workspace.CurrentCamera
			local dir = Vector3.new(0,0,0)
			if ctrl.f > 0 then dir = dir + cam.CFrame.LookVector end
			if ctrl.b > 0 then dir = dir - cam.CFrame.LookVector end
			if ctrl.r > 0 then dir = dir + cam.CFrame.RightVector end
			if ctrl.l > 0 then dir = dir - cam.CFrame.RightVector end
			if ctrl.u > 0 then dir = dir + Vector3.new(0,1,0) end
			if ctrl.d > 0 then dir = dir - Vector3.new(0,1,0) end
			if dir.Magnitude > 0 then dir = dir.Unit end
			bv.Velocity = dir * speed
			bg.CFrame = cam.CFrame
		end

		local c1 = UserInputService.InputBegan:Connect(function(i, g)
			if g then return end
			if i.KeyCode == Enum.KeyCode.W then ctrl.f = 1
			elseif i.KeyCode == Enum.KeyCode.S then ctrl.b = 1
			elseif i.KeyCode == Enum.KeyCode.A then ctrl.l = 1
			elseif i.KeyCode == Enum.KeyCode.D then ctrl.r = 1
			elseif i.KeyCode == Enum.KeyCode.Space then ctrl.u = 1
			elseif i.KeyCode == Enum.KeyCode.LeftShift or i.KeyCode == Enum.KeyCode.RightShift then ctrl.d = 1 end
		end)

		local c2 = UserInputService.InputEnded:Connect(function(i)
			if i.KeyCode == Enum.KeyCode.W then ctrl.f = 0
			elseif i.KeyCode == Enum.KeyCode.S then ctrl.b = 0
			elseif i.KeyCode == Enum.KeyCode.A then ctrl.l = 0
			elseif i.KeyCode == Enum.KeyCode.D then ctrl.r = 0
			elseif i.KeyCode == Enum.KeyCode.Space then ctrl.u = 0
			elseif i.KeyCode == Enum.KeyCode.LeftShift or i.KeyCode == Enum.KeyCode.RightShift then ctrl.d = 0 end
		end)

		local c3 = RunService.Heartbeat:Connect(update)

		ActiveEffects.Fly = {
			Stop = function()
				c1:Disconnect() c2:Disconnect() c3:Disconnect()
				if bg and bg.Parent then bg:Destroy() end
				if bv and bv.Parent then bv:Destroy() end
			end
		}

		Notify("Flying! WASD + Space/Shift", CONFIG.Theme.Success)
	end)

	Cmd("unfly", {"nofly"}, "Stop flying", 1, function(args)
		if ActiveEffects.Fly then
			ActiveEffects.Fly.Stop()
			ActiveEffects.Fly = nil
			Notify("Flying OFF", CONFIG.Theme.Warning)
		end
	end)

	Cmd("noclip", {}, "Walk through walls", 1, function(args)
		if ActiveEffects.Noclip then return end
		ActiveEffects.Noclip = true
		local c = RunService.Stepped:Connect(function()
			if not ActiveEffects.Noclip then return end
			if player.Character then
				for _, p in ipairs(player.Character:GetDescendants()) do
					if p:IsA("BasePart") then p.CanCollide = false end
				end
			end
		end)
		ActiveEffects.NoclipConn = c
		Notify("Noclip ON", CONFIG.Theme.Success)
	end)

	Cmd("clip", {"unnoclip"}, "Disable noclip", 1, function(args)
		ActiveEffects.Noclip = nil
		if ActiveEffects.NoclipConn then
			ActiveEffects.NoclipConn:Disconnect()
			ActiveEffects.NoclipConn = nil
		end
		if player.Character then
			for _, p in ipairs(player.Character:GetDescendants()) do
				if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
					p.CanCollide = true
				end
			end
		end
		Notify("Noclip OFF", CONFIG.Theme.Warning)
	end)

	-- CHARACTER
	Cmd("god", {"godmode"}, "Invincibility", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.MaxHealth = math.huge
			player.Character.Humanoid.Health = math.huge
			Notify("God mode ON", CONFIG.Theme.Success)
		end
	end)

	Cmd("ungod", {"nogod"}, "Remove god", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.MaxHealth = 100
			player.Character.Humanoid.Health = 100
			Notify("God mode OFF", CONFIG.Theme.Warning)
		end
	end)

	Cmd("heal", {"hp"}, "Full health", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.Health = player.Character.Humanoid.MaxHealth
			Notify("Healed!", CONFIG.Theme.Success)
		end
	end)

	Cmd("kill", {"slay"}, "Kill yourself", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.Health = 0
			Notify("Killed", CONFIG.Theme.Success)
		end
	end)

	Cmd("respawn", {"res", "reset"}, "Respawn", 1, function(args)
		player:LoadCharacter()
		Notify("Respawned", CONFIG.Theme.Success)
	end)

	Cmd("refresh", {"re"}, "Refresh at position", 1, function(args)
		local pos = player.Character and player.Character:FindFirstChild("HumanoidRootPart") and 
			player.Character.HumanoidRootPart.CFrame
		player:LoadCharacter()
		if pos then
			task.wait(0.1)
			if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
				player.Character.HumanoidRootPart.CFrame = pos
			end
		end
		Notify("Refreshed", CONFIG.Theme.Success)
	end)

	-- VISIBILITY
	Cmd("invisible", {"invis"}, "Invisible", 1, function(args)
		if player.Character then
			for _, p in ipairs(player.Character:GetDescendants()) do
				if p:IsA("BasePart") then p.Transparency = 1
				elseif p:IsA("Decal") then p.Transparency = 1 end
			end
			Notify("Invisible", CONFIG.Theme.Success)
		end
	end)

	Cmd("visible", {"vis"}, "Visible", 1, function(args)
		if player.Character then
			for _, p in ipairs(player.Character:GetDescendants()) do
				if p:IsA("BasePart") then
					p.Transparency = p.Name == "HumanoidRootPart" and 1 or 0
				elseif p:IsA("Decal") then p.Transparency = 0 end
			end
			Notify("Visible", CONFIG.Theme.Success)
		end
	end)

	Cmd("freeze", {"fr"}, "Freeze", 1, function(args)
		if player.Character then
			for _, p in ipairs(player.Character:GetDescendants()) do
				if p:IsA("BasePart") then p.Anchored = true end
			end
			Notify("Frozen", CONFIG.Theme.Success)
		end
	end)

	Cmd("thaw", {"unfreeze"}, "Unfreeze", 1, function(args)
		if player.Character then
			for _, p in ipairs(player.Character:GetDescendants()) do
				if p:IsA("BasePart") then p.Anchored = false end
			end
			Notify("Thawed", CONFIG.Theme.Success)
		end
	end)

	Cmd("sit", {}, "Sit", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.Sit = true
			Notify("Sitting", CONFIG.Theme.Success)
		end
	end)

	Cmd("unsit", {"stand"}, "Stand", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.Sit = false
			Notify("Standing", CONFIG.Theme.Success)
		end
	end)

	-- EFFECTS
	Cmd("fire", {}, "Add fire", 1, function(args)
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			Instance.new("Fire", player.Character.HumanoidRootPart)
			Notify("Fire added", CONFIG.Theme.Success)
		end
	end)

	Cmd("unfire", {}, "Remove fire", 1, function(args)
		if player.Character then
			for _, o in ipairs(player.Character:GetDescendants()) do
				if o:IsA("Fire") then o:Destroy() end
			end
			Notify("Fire removed", CONFIG.Theme.Success)
		end
	end)

	Cmd("smoke", {}, "Add smoke", 1, function(args)
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			Instance.new("Smoke", player.Character.HumanoidRootPart)
			Notify("Smoke added", CONFIG.Theme.Success)
		end
	end)

	Cmd("unsmoke", {}, "Remove smoke", 1, function(args)
		if player.Character then
			for _, o in ipairs(player.Character:GetDescendants()) do
				if o:IsA("Smoke") then o:Destroy() end
			end
			Notify("Smoke removed", CONFIG.Theme.Success)
		end
	end)

	Cmd("sparkles", {"sparkle"}, "Add sparkles", 1, function(args)
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			Instance.new("Sparkles", player.Character.HumanoidRootPart)
			Notify("Sparkles added", CONFIG.Theme.Success)
		end
	end)

	Cmd("unsparkles", {"unsparkle"}, "Remove sparkles", 1, function(args)
		if player.Character then
			for _, o in ipairs(player.Character:GetDescendants()) do
				if o:IsA("Sparkles") then o:Destroy() end
			end
			Notify("Sparkles removed", CONFIG.Theme.Success)
		end
	end)

	Cmd("ff", {"forcefield"}, "Forcefield", 1, function(args)
		if player.Character then
			Instance.new("ForceField", player.Character)
			Notify("Forcefield ON", CONFIG.Theme.Success)
		end
	end)

	Cmd("unff", {}, "Remove forcefield", 1, function(args)
		if player.Character then
			for _, f in ipairs(player.Character:GetChildren()) do
				if f:IsA("ForceField") then f:Destroy() end
			end
			Notify("Forcefield OFF", CONFIG.Theme.Success)
		end
	end)

	-- FUN
	Cmd("explode", {"boom"}, "Explode!", 1, function(args)
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			local e = Instance.new("Explosion")
			e.Position = player.Character.HumanoidRootPart.Position
			e.Parent = workspace
			Notify("BOOM!", CONFIG.Theme.Success)
		end
	end)

	Cmd("fling", {}, "Fling", 1, function(args)
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			local bv = Instance.new("BodyVelocity")
			bv.MaxForce = Vector3.new(1,1,1) * math.huge
			bv.Velocity = Vector3.new(0, 200, 0)
			bv.Parent = player.Character.HumanoidRootPart
			task.delay(0.5, function() bv:Destroy() end)
			Notify("Flung!", CONFIG.Theme.Success)
		end
	end)

	Cmd("ragdoll", {}, "Ragdoll", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.PlatformStand = true
			Notify("Ragdolled", CONFIG.Theme.Success)
		end
	end)

	Cmd("unragdoll", {}, "Unragdoll", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.PlatformStand = false
			Notify("Unragdolled", CONFIG.Theme.Success)
		end
	end)

	-- HEAD SIZE (R6/R15)
	Cmd("bighead", {}, "Big head", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Head") then
			local h = player.Character.Head
			if h:FindFirstChildOfClass("SpecialMesh") then
				h:FindFirstChildOfClass("SpecialMesh").Scale = Vector3.new(3,3,3)
			end
			if player.Character:FindFirstChild("Humanoid") then
				local hum = player.Character.Humanoid
				if hum:FindFirstChild("HeadScale") then hum.HeadScale.Value = 3 end
			end
			Notify("Big head", CONFIG.Theme.Success)
		end
	end)

	Cmd("normalhead", {}, "Normal head", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Head") then
			local h = player.Character.Head
			if h:FindFirstChildOfClass("SpecialMesh") then
				h:FindFirstChildOfClass("SpecialMesh").Scale = Vector3.new(1.25,1.25,1.25)
			end
			if player.Character:FindFirstChild("Humanoid") then
				local hum = player.Character.Humanoid
				if hum:FindFirstChild("HeadScale") then hum.HeadScale.Value = 1 end
			end
			Notify("Normal head", CONFIG.Theme.Success)
		end
	end)

	Cmd("smallhead", {}, "Small head", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Head") then
			local h = player.Character.Head
			if h:FindFirstChildOfClass("SpecialMesh") then
				h:FindFirstChildOfClass("SpecialMesh").Scale = Vector3.new(0.5,0.5,0.5)
			end
			if player.Character:FindFirstChild("Humanoid") then
				local hum = player.Character.Humanoid
				if hum:FindFirstChild("HeadScale") then hum.HeadScale.Value = 0.5 end
			end
			Notify("Small head", CONFIG.Theme.Success)
		end
	end)

	Cmd("spin", {}, "Spin", 1, function(args)
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			local s = Instance.new("BodyAngularVelocity")
			s.MaxTorque = Vector3.new(0, math.huge, 0)
			s.AngularVelocity = Vector3.new(0, 20, 0)
			s.Parent = player.Character.HumanoidRootPart
			ActiveEffects.Spin = s
			Notify("Spinning", CONFIG.Theme.Success)
		end
	end)

	Cmd("unspin", {}, "Stop spin", 1, function(args)
		if ActiveEffects.Spin then
			ActiveEffects.Spin:Destroy()
			ActiveEffects.Spin = nil
			Notify("Spin stopped", CONFIG.Theme.Success)
		end
	end)

	Cmd("flash", {}, "Flash light", 1, function(args)
		if player.Character and player.Character:FindFirstChild("HumanoidRootPart") then
			local l = Instance.new("PointLight")
			l.Brightness = 10
			l.Range = 60
			l.Parent = player.Character.HumanoidRootPart
			spawn(function()
				for i = 1, 10 do
					l.Enabled = not l.Enabled
					task.wait(0.1)
				end
				l:Destroy()
			end)
			Notify("Flashing!", CONFIG.Theme.Success)
		end
	end)

	Cmd("trip", {}, "Trip", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.Sit = true
			task.delay(0.5, function()
				if player.Character and player.Character:FindFirstChild("Humanoid") then
					player.Character.Humanoid.Sit = false
				end
			end)
			Notify("Oops!", CONFIG.Theme.Success)
		end
	end)

	Cmd("stun", {}, "Stun", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.PlatformStand = true
			Notify("Stunned", CONFIG.Theme.Success)
		end
	end)

	Cmd("unstun", {}, "Unstun", 1, function(args)
		if player.Character and player.Character:FindFirstChild("Humanoid") then
			player.Character.Humanoid.PlatformStand = false
			Notify("Unstunned", CONFIG.Theme.Success)
		end
	end)

	-- TOOLS
	Cmd("removetools", {"rtools", "notools"}, "Remove tools", 1, function(args)
		if player.Backpack then player.Backpack:ClearAllChildren() end
		if player.Character then
			for _, t in ipairs(player.Character:GetChildren()) do
				if t:IsA("Tool") then t:Destroy() end
			end
		end
		Notify("Tools removed", CONFIG.Theme.Success)
	end)

	Cmd("btools", {}, "Building tools", 3, function(args)
		for _, name in ipairs({"Clone", "Hammer", "Resize"}) do
			local t = Instance.new("Tool")
			t.Name = name
			t.RequiresHandle = false
			t.Parent = player.Backpack
		end
		Notify("Building tools", CONFIG.Theme.Success)
	end)

	-- UTILITY
	Cmd("prefix", {}, "Change prefix (:prefix !)", 1, function(args)
		if args[1] then
			CONFIG.Prefix = args[1]
			Notify("Prefix: " .. args[1], CONFIG.Theme.Success)
		end
	end)

	Cmd("clear", {"clearchat"}, "Clear chat", 0, function(args)
		StarterGui:SetCore("ChatMakeSystemMessage", {
			Text = string.rep("\n", 100),
			Color = Color3.new(1,1,1),
			Font = Enum.Font.SourceSans,
			FontSize = Enum.FontSize.Size24
		})
		Notify("Chat cleared", CONFIG.Theme.Success)
	end)

	Cmd("credits", {}, "Show credits", 0, function(args)
		Notify("Check Credits tab! Press '" .. CONFIG.ConsoleKey.Name .. "'", CONFIG.Theme.Accent)
	end)

end

-- PARSE COMMAND
local function Parse(text)
	if not text:sub(1, #CONFIG.Prefix) == CONFIG.Prefix then return end

	local args = {}
	for arg in text:sub(#CONFIG.Prefix + 1):gmatch("%S+") do
		table.insert(args, arg)
	end

	if #args == 0 then return end

	local cmdName = args[1]:lower()
	table.remove(args, 1)

	local cmd = Commands[cmdName]
	if cmd then
		local ok, err = pcall(cmd.Func, args)
		if not ok then
			Notify("Error: " .. tostring(err), CONFIG.Theme.Error)
		end
		table.insert(CommandHistory, text)
	else
		Notify("Unknown: " .. cmdName, CONFIG.Theme.Error)
	end
end

-- CREATE UI
local function CreateUI()
	GUI = Instance.new("ScreenGui")
	GUI.Name = "AAAdminGUI"
	GUI.ResetOnSpawn = false
	GUI.DisplayOrder = 10
	GUI.IgnoreGuiInset = true
	GUI.Parent = player:WaitForChild("PlayerGui")

	-- CONSOLE
	local console = Instance.new("Frame")
	console.Name = "Console"
	console.Size = UDim2.new(0, 700, 0, 500)
	console.Position = UDim2.new(0.5, -350, 0.5, -250)
	console.BackgroundColor3 = CONFIG.Theme.Primary
	console.BorderSizePixel = 0
	console.Visible = false
	console.Parent = GUI
	Instance.new("UICorner", console).CornerRadius = UDim.new(0, 15)

	-- TITLE BAR
	local titleBar = Instance.new("Frame")
	titleBar.Size = UDim2.new(1, 0, 0, 50)
	titleBar.BackgroundColor3 = CONFIG.Theme.Secondary
	titleBar.BorderSizePixel = 0
	titleBar.Parent = console
	Instance.new("UICorner", titleBar).CornerRadius = UDim.new(0, 15)

	local titleCover = Instance.new("Frame")
	titleCover.Size = UDim2.new(1, 0, 0, 25)
	titleCover.Position = UDim2.new(0, 0, 1, -25)
	titleCover.BackgroundColor3 = CONFIG.Theme.Secondary
	titleCover.BorderSizePixel = 0
	titleCover.Parent = titleBar

	local titleText = Instance.new("TextLabel")
	titleText.Text = "⚡ AA ADMIN v3.0"
	titleText.Size = UDim2.new(0.5, 0, 1, 0)
	titleText.Position = UDim2.new(0, 20, 0, 0)
	titleText.BackgroundTransparency = 1
	titleText.Font = Enum.Font.GothamBold
	titleText.TextSize = 20
	titleText.TextColor3 = CONFIG.Theme.Text
	titleText.TextXAlignment = Enum.TextXAlignment.Left
	titleText.Parent = titleBar

	local badge = Instance.new("TextLabel")
	badge.Text = AdminLevels[GetAdminLevel()]
	badge.Size = UDim2.new(0, 110, 0, 32)
	badge.Position = UDim2.new(1, -260, 0.5, -16)
	badge.BackgroundColor3 = CONFIG.Theme.Accent
	badge.Font = Enum.Font.GothamBold
	badge.TextSize = 14
	badge.TextColor3 = CONFIG.Theme.Text
	badge.Parent = titleBar
	Instance.new("UICorner", badge).CornerRadius = UDim.new(0, 8)

	local closeBtn = Instance.new("TextButton")
	closeBtn.Size = UDim2.new(0, 40, 0, 40)
	closeBtn.Position = UDim2.new(1, -45, 0.5, -20)
	closeBtn.BackgroundColor3 = CONFIG.Theme.Error
	closeBtn.Text = "×"
	closeBtn.TextColor3 = CONFIG.Theme.Text
	closeBtn.Font = Enum.Font.GothamBold
	closeBtn.TextSize = 28
	closeBtn.BorderSizePixel = 0
	closeBtn.Parent = titleBar
	Instance.new("UICorner", closeBtn).CornerRadius = UDim.new(0, 10)
	closeBtn.MouseButton1Click:Connect(function() console.Visible = false end)

	-- TABS
	local tabCont = Instance.new("Frame")
	tabCont.Size = UDim2.new(1, -40, 0, 50)
	tabCont.Position = UDim2.new(0, 20, 0, 60)
	tabCont.BackgroundTransparency = 1
	tabCont.Parent = console

	local helpTab = Instance.new("TextButton")
	helpTab.Name = "HelpTab"
	helpTab.Size = UDim2.new(0, 150, 0, 38)
	helpTab.BackgroundColor3 = CONFIG.Theme.Accent
	helpTab.Text = "📋 Help"
	helpTab.TextColor3 = CONFIG.Theme.Text
	helpTab.Font = Enum.Font.GothamBold
	helpTab.TextSize = 16
	helpTab.BorderSizePixel = 0
	helpTab.Parent = tabCont
	Instance.new("UICorner", helpTab).CornerRadius = UDim.new(0, 10)

	local creditsTab = Instance.new("TextButton")
	creditsTab.Name = "CreditsTab"
	creditsTab.Size = UDim2.new(0, 150, 0, 38)
	creditsTab.Position = UDim2.new(0, 160, 0, 0)
	creditsTab.BackgroundColor3 = CONFIG.Theme.Primary
	creditsTab.Text = "⭐ Credits"
	creditsTab.TextColor3 = CONFIG.Theme.TextDark
	creditsTab.Font = Enum.Font.GothamBold
	creditsTab.TextSize = 16
	creditsTab.BorderSizePixel = 0
	creditsTab.Parent = tabCont
	Instance.new("UICorner", creditsTab).CornerRadius = UDim.new(0, 10)

	-- HELP PAGE
	local helpPage = Instance.new("ScrollingFrame")
	helpPage.Name = "HelpPage"
	helpPage.Size = UDim2.new(1, -40, 1, -130)
	helpPage.Position = UDim2.new(0, 20, 0, 120)
	helpPage.BackgroundTransparency = 1
	helpPage.BorderSizePixel = 0
	helpPage.ScrollBarThickness = 8
	helpPage.ScrollBarImageColor3 = CONFIG.Theme.Accent
	helpPage.CanvasSize = UDim2.new(0, 0, 0, 0)
	helpPage.Visible = true
	helpPage.Parent = console

	local helpLayout = Instance.new("UIListLayout")
	helpLayout.Padding = UDim.new(0, 10)
	helpLayout.Parent = helpPage
	helpLayout:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(function()
		helpPage.CanvasSize = UDim2.new(0, 0, 0, helpLayout.AbsoluteContentSize.Y + 20)
	end)

	-- Add commands to help
	local displayed = {}
	for name, cmd in pairs(Commands) do
		if name == cmd.Name:lower() and not displayed[cmd.Name] and cmd.Level <= GetAdminLevel() then
			displayed[cmd.Name] = true

			local f = Instance.new("Frame")
			f.Size = UDim2.new(1, -10, 0, 60)
			f.BackgroundColor3 = CONFIG.Theme.Secondary
			f.BorderSizePixel = 0
			f.Parent = helpPage
			Instance.new("UICorner", f).CornerRadius = UDim.new(0, 8)

			local cmdL = Instance.new("TextLabel")
			cmdL.Text = CONFIG.Prefix .. cmd.Name
			cmdL.Size = UDim2.new(0.5, 0, 0, 25)
			cmdL.Position = UDim2.new(0, 15, 0, 8)
			cmdL.BackgroundTransparency = 1
			cmdL.Font = Enum.Font.GothamBold
			cmdL.TextSize = 15
			cmdL.TextColor3 = CONFIG.Theme.Accent
			cmdL.TextXAlignment = Enum.TextXAlignment.Left
			cmdL.Parent = f

			local descL = Instance.new("TextLabel")
			descL.Text = cmd.Desc
			descL.Size = UDim2.new(1, -30, 0, 22)
			descL.Position = UDim2.new(0, 15, 0, 33)
			descL.BackgroundTransparency = 1
			descL.Font = Enum.Font.Gotham
			descL.TextSize = 12
			descL.TextColor3 = CONFIG.Theme.TextDark
			descL.TextXAlignment = Enum.TextXAlignment.Left
			descL.Parent = f

			local lvlB = Instance.new("TextLabel")
			lvlB.Text = AdminLevels[cmd.Level]
			lvlB.Size = UDim2.new(0, 85, 0, 22)
			lvlB.Position = UDim2.new(1, -95, 0, 8)
			lvlB.BackgroundColor3 = CONFIG.Theme.Primary
			lvlB.Font = Enum.Font.Gotham
			lvlB.TextSize = 11
			lvlB.TextColor3 = CONFIG.Theme.Text
			lvlB.Parent = f
			Instance.new("UICorner", lvlB).CornerRadius = UDim.new(0, 5)
		end
	end

	-- CREDITS PAGE
	local creditsPage = Instance.new("Frame")
	creditsPage.Name = "CreditsPage"
	creditsPage.Size = UDim2.new(1, -40, 1, -130)
	creditsPage.Position = UDim2.new(0, 20, 0, 120)
	creditsPage.BackgroundTransparency = 1
	creditsPage.Visible = false
	creditsPage.Parent = console

	local cTitle = Instance.new("TextLabel")
	cTitle.Text = "AA ADMIN SYSTEM"
	cTitle.Size = UDim2.new(1, 0, 0, 50)
	cTitle.Position = UDim2.new(0, 0, 0, 30)
	cTitle.BackgroundTransparency = 1
	cTitle.Font = Enum.Font.GothamBold
	cTitle.TextSize = 32
	cTitle.TextColor3 = CONFIG.Theme.Text
	cTitle.Parent = creditsPage

	local createdBy = Instance.new("TextLabel")
	createdBy.Text = "Created by"
	createdBy.Size = UDim2.new(1, 0, 0, 30)
	createdBy.Position = UDim2.new(0, 0, 0, 100)
	createdBy.BackgroundTransparency = 1
	createdBy.Font = Enum.Font.Gotham
	createdBy.TextSize = 18
	createdBy.TextColor3 = CONFIG.Theme.TextDark
	createdBy.Parent = creditsPage

	-- RAINBOW NAME
	local rainbowName = Instance.new("TextLabel")
	rainbowName.Text = "Hunter09aden091"
	rainbowName.Size = UDim2.new(1, 0, 0, 50)
	rainbowName.Position = UDim2.new(0, 0, 0, 140)
	rainbowName.BackgroundTransparency = 1
	rainbowName.Font = Enum.Font.GothamBold
	rainbowName.TextSize = 28
	rainbowName.Parent = creditsPage

	local gradient = Instance.new("UIGradient")
	gradient.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 0, 0)),
		ColorSequenceKeypoint.new(0.17, Color3.fromRGB(255, 165, 0)),
		ColorSequenceKeypoint.new(0.33, Color3.fromRGB(255, 255, 0)),
		ColorSequenceKeypoint.new(0.5, Color3.fromRGB(0, 255, 0)),
		ColorSequenceKeypoint.new(0.67, Color3.fromRGB(0, 191, 255)),
		ColorSequenceKeypoint.new(0.83, Color3.fromRGB(138, 43, 226)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 0, 0))
	})
	gradient.Parent = rainbowName

	spawn(function()
		while rainbowName and rainbowName.Parent do
			for i = 0, 360, 2 do
				if not rainbowName or not rainbowName.Parent then break end
				gradient.Rotation = i
				task.wait(0.03)
			end
		end
	end)

	local version = Instance.new("TextLabel")
	version.Text = "Version 3.0 - Ultimate Edition"
	version.Size = UDim2.new(1, 0, 0, 25)
	version.Position = UDim2.new(0, 0, 0, 200)
	version.BackgroundTransparency = 1
	version.Font = Enum.Font.Gotham
	version.TextSize = 16
	version.TextColor3 = CONFIG.Theme.TextDark
	version.Parent = creditsPage

	local features = Instance.new("TextLabel")
	features.Text = "✨ 50+ Commands\n🎯 Smart Autocomplete\n🚀 Smooth Flying\n💫 All Working"
	features.Size = UDim2.new(1, 0, 0, 80)
	features.Position = UDim2.new(0, 0, 0, 240)
	features.BackgroundTransparency = 1
	features.Font = Enum.Font.Gotham
	features.TextSize = 14
	features.TextColor3 = CONFIG.Theme.Text
	features.Parent = creditsPage

	-- TAB SWITCHING
	local function switchTab(tab)
		if tab == "help" then
			helpTab.BackgroundColor3 = CONFIG.Theme.Accent
			helpTab.TextColor3 = CONFIG.Theme.Text
			creditsTab.BackgroundColor3 = CONFIG.Theme.Primary
			creditsTab.TextColor3 = CONFIG.Theme.TextDark
			helpPage.Visible = true
			creditsPage.Visible = false
		else
			helpTab.BackgroundColor3 = CONFIG.Theme.Primary
			helpTab.TextColor3 = CONFIG.Theme.TextDark
			creditsTab.BackgroundColor3 = CONFIG.Theme.Accent
			creditsTab.TextColor3 = CONFIG.Theme.Text
			helpPage.Visible = false
			creditsPage.Visible = true
		end
	end

	helpTab.MouseButton1Click:Connect(function() switchTab("help") end)
	creditsTab.MouseButton1Click:Connect(function() switchTab("credits") end)

	-- COMMAND BAR
	local cmdBar = Instance.new("Frame")
	cmdBar.Size = UDim2.new(0, 600, 0, 50)
	cmdBar.Position = UDim2.new(0.5, -300, 1, -70)
	cmdBar.BackgroundColor3 = CONFIG.Theme.Primary
	cmdBar.BorderSizePixel = 0
	cmdBar.Visible = false
	cmdBar.Parent = GUI
	Instance.new("UICorner", cmdBar).CornerRadius = UDim.new(0, 12)

	local input = Instance.new("TextBox")
	input.Size = UDim2.new(1, -30, 1, 0)
	input.Position = UDim2.new(0, 15, 0, 0)
	input.BackgroundTransparency = 1
	input.Font = Enum.Font.Gotham
	input.TextSize = 18
	input.TextColor3 = CONFIG.Theme.Text
	input.PlaceholderText = "Type command... (Press " .. CONFIG.ConsoleKey.Name .. " or ;)"
	input.PlaceholderColor3 = CONFIG.Theme.TextDark
	input.Text = ""
	input.ClearTextOnFocus = false
	input.Parent = cmdBar

	-- AUTOCOMPLETE
	local autocomplete = Instance.new("ScrollingFrame")
	autocomplete.Size = UDim2.new(1, 0, 0, 0)
	autocomplete.Position = UDim2.new(0, 0, 0, -10)
	autocomplete.BackgroundColor3 = CONFIG.Theme.Secondary
	autocomplete.BorderSizePixel = 0
	autocomplete.ScrollBarThickness = 6
	autocomplete.ScrollBarImageColor3 = CONFIG.Theme.Accent
	autocomplete.Visible = false
	autocomplete.CanvasSize = UDim2.new(0, 0, 0, 0)
	autocomplete.Parent = cmdBar
	Instance.new("UICorner", autocomplete).CornerRadius = UDim.new(0, 10)

	local acLayout = Instance.new("UIListLayout")
	acLayout.Padding = UDim.new(0, 3)
	acLayout.Parent = autocomplete

	-- Update autocomplete
	input:GetPropertyChangedSignal("Text"):Connect(function()
		for _, c in ipairs(autocomplete:GetChildren()) do
			if c:IsA("TextButton") then c:Destroy() end
		end

		local text = input.Text
		if text == "" or not text:sub(1, #CONFIG.Prefix) == CONFIG.Prefix then
			autocomplete.Visible = false
			autocomplete.Size = UDim2.new(1, 0, 0, 0)
			return
		end

		local search = text:sub(#CONFIG.Prefix + 1):lower()
		local matches = {}
		local shown = {}

		for name, cmd in pairs(Commands) do
			if name == cmd.Name:lower() and not shown[cmd.Name] and cmd.Level <= GetAdminLevel() and FuzzyMatch(cmd.Name, search) then
				shown[cmd.Name] = true
				table.insert(matches, cmd)
			end
		end

		table.sort(matches, function(a, b) return a.Name < b.Name end)

		if #matches > 0 then
			autocomplete.Visible = true
			local h = math.min(#matches * 45, 225)
			autocomplete.Size = UDim2.new(1, 0, 0, h)
			autocomplete.Position = UDim2.new(0, 0, 0, -h - 15)
			autocomplete.CanvasSize = UDim2.new(0, 0, 0, #matches * 45)

			for i, cmd in ipairs(matches) do
				if i <= 15 then
					local btn = Instance.new("TextButton")
					btn.Size = UDim2.new(1, -12, 0, 40)
					btn.Position = UDim2.new(0, 6, 0, (i-1) * 45)
					btn.BackgroundColor3 = CONFIG.Theme.Primary
					btn.BorderSizePixel = 0
					btn.Text = ""
					btn.Parent = autocomplete
					Instance.new("UICorner", btn).CornerRadius = UDim.new(0, 8)

					local cText = Instance.new("TextLabel")
					cText.Text = CONFIG.Prefix .. cmd.Name
					cText.Size = UDim2.new(0.6, 0, 0.5, 0)
					cText.Position = UDim2.new(0, 12, 0, 2)
					cText.BackgroundTransparency = 1
					cText.Font = Enum.Font.GothamBold
					cText.TextSize = 14
					cText.TextColor3 = CONFIG.Theme.Accent
					cText.TextXAlignment = Enum.TextXAlignment.Left
					cText.Parent = btn

					local dText = Instance.new("TextLabel")
					dText.Text = cmd.Desc
					dText.Size = UDim2.new(1, -25, 0.5, 0)
					dText.Position = UDim2.new(0, 12, 0.5, -2)
					dText.BackgroundTransparency = 1
					dText.Font = Enum.Font.Gotham
					dText.TextSize = 11
					dText.TextColor3 = CONFIG.Theme.TextDark
					dText.TextXAlignment = Enum.TextXAlignment.Left
					dText.Parent = btn

					btn.MouseButton1Click:Connect(function()
						input.Text = CONFIG.Prefix .. cmd.Name .. " "
						input:CaptureFocus()
						autocomplete.Visible = false
					end)
				end
			end
		else
			autocomplete.Visible = false
			autocomplete.Size = UDim2.new(1, 0, 0, 0)
		end
	end)

	input.FocusLost:Connect(function(enter)
		if enter and input.Text ~= "" then
			Parse(input.Text)
			input.Text = ""
			autocomplete.Visible = false
		end
	end)

	-- CONTROLS
	local histIdx = 0
	UserInputService.InputBegan:Connect(function(i, g)
		if g then return end

		if i.KeyCode == CONFIG.ConsoleKey then
			console.Visible = not console.Visible
		elseif i.KeyCode == Enum.KeyCode.Semicolon then
			cmdBar.Visible = not cmdBar.Visible
			if cmdBar.Visible then input:CaptureFocus() end
		elseif i.KeyCode == Enum.KeyCode.Up and input:IsFocused() then
			if histIdx < #CommandHistory then
				histIdx = histIdx + 1
				input.Text = CommandHistory[#CommandHistory - histIdx + 1] or ""
			end
		elseif i.KeyCode == Enum.KeyCode.Down and input:IsFocused() then
			if histIdx > 0 then
				histIdx = histIdx - 1
				input.Text = histIdx == 0 and "" or CommandHistory[#CommandHistory - histIdx + 1] or ""
			end
		end
	end)
end

-- CHAT COMMANDS
player.Chatted:Connect(function(msg)
	if msg:sub(1, #CONFIG.Prefix) == CONFIG.Prefix then
		Parse(msg)
	end
end)

-- INIT
print("=== AA ADMIN SYSTEM ===")
print("Your UserID: " .. player.UserId)
print("Admin Level: " .. GetAdminLevel())

if GetAdminLevel() == 0 then
	warn("⚠️ NOT ADMIN! Add: [" .. player.UserId .. "] = 5,")
	return
end

RegisterAllCommands()
CreateUI()
Notify("AA Admin loaded! Press '" .. CONFIG.ConsoleKey.Name .. "' or :cmds", CONFIG.Theme.Accent)
print("✅ Loaded successfully!")

-- LocalScript in StarterPlayerScripts
local Players = game:GetService("Players")
local MarketplaceService = game:GetService("MarketplaceService")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local donationItems = {
    {name = "Small Tip", price = 25, productId = 0000000, color = Color3.fromRGB(100, 200, 100), emoji = "💚"},
    {name = "Medium Tip", price = 100, productId = 0000000, color = Color3.fromRGB(100, 150, 255), emoji = "💙"},
    {name = "Large Donation", price = 250, productId = 0000000, color = Color3.fromRGB(200, 100, 255), emoji = "💜"},
    {name = "Mega Donation", price = 500, productId = 0000000, color = Color3.fromRGB(255, 200, 50), emoji = "⭐"},
}

-- Animation presets
local tweenInfo = TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
local fastTween = TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local slowTween = TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)

-- Get or create RemoteEvent for donation tracking
local getDonationData
local updateLeaderboard
if not ReplicatedStorage:FindFirstChild("GetDonationData") then
    getDonationData = Instance.new("RemoteFunction")
    getDonationData.Name = "GetDonationData"
    getDonationData.Parent = ReplicatedStorage
else
    getDonationData = ReplicatedStorage:FindFirstChild("GetDonationData")
end

if not ReplicatedStorage:FindFirstChild("UpdateLeaderboard") then
    updateLeaderboard = Instance.new("RemoteEvent")
    updateLeaderboard.Name = "UpdateLeaderboard"
    updateLeaderboard.Parent = ReplicatedStorage
else
    updateLeaderboard = ReplicatedStorage:FindFirstChild("UpdateLeaderboard")
end

-- Confetti particle system
local function createConfetti(parent, color)
    for i = 1, 80 do
        local confetti = Instance.new("Frame")
        confetti.Size = UDim2.new(0, math.random(10, 20), 0, math.random(10, 20))
        confetti.Position = UDim2.new(0.5, 0, 0.5, 0)
        confetti.AnchorPoint = Vector2.new(0.5, 0.5)
        confetti.BackgroundColor3 = Color3.fromRGB(
            math.random(150, 255),
            math.random(150, 255),
            math.random(150, 255)
        )
        confetti.BorderSizePixel = 0
        confetti.ZIndex = 99
        confetti.Rotation = math.random(0, 360)
        confetti.Parent = parent
        
        local corner = Instance.new("UICorner")
        corner.CornerRadius = UDim.new(0, 4)
        corner.Parent = confetti
        
        local gradient = Instance.new("UIGradient")
        gradient.Color = ColorSequence.new{
            ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 255, 255)),
            ColorSequenceKeypoint.new(1, confetti.BackgroundColor3)
        }
        gradient.Rotation = math.random(0, 360)
        gradient.Parent = confetti
        
        local angle = math.rad(math.random(0, 360))
        local distance = math.random(200, 600)
        local endX = math.cos(angle) * distance
        local endY = math.sin(angle) * distance
        
        local moveTween = TweenService:Create(confetti, TweenInfo.new(
            math.random(10, 15) / 10,
            Enum.EasingStyle.Quad,
            Enum.EasingDirection.Out
        ), {
            Position = UDim2.new(0.5, endX, 0.5, endY),
            Rotation = confetti.Rotation + math.random(-720, 720)
        })
        
        local fadeTween = TweenService:Create(confetti, TweenInfo.new(
            0.6,
            Enum.EasingStyle.Quad,
            Enum.EasingDirection.In
        ), {
            BackgroundTransparency = 1
        })
        
        moveTween:Play()
        task.wait(0.01)
        task.wait(0.5)
        fadeTween:Play()
        
        task.spawn(function()
            task.wait(0.6)
            confetti:Destroy()
        end)
    end
end

-- Success message
local function showSuccessMessage(parent, itemName, color)
    local successFrame = Instance.new("Frame")
    successFrame.Name = "SuccessMessage"
    successFrame.Size = UDim2.new(0, 500, 0, 200)
    successFrame.Position = UDim2.new(0.5, 0, 0.5, 0)
    successFrame.AnchorPoint = Vector2.new(0.5, 0.5)
    successFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 40)
    successFrame.BorderSizePixel = 0
    successFrame.ZIndex = 100
    successFrame.BackgroundTransparency = 1
    successFrame.Parent = parent
    
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 15)
    corner.Parent = successFrame
    
    local glow = Instance.new("UIStroke")
    glow.Color = color
    glow.Thickness = 4
    glow.Transparency = 0
    glow.Parent = successFrame
    
    local glow2 = Instance.new("UIStroke")
    glow2.Color = Color3.fromRGB(255, 255, 255)
    glow2.Thickness = 2
    glow2.Transparency = 0.5
    glow2.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
    glow2.Parent = successFrame
    
    -- Sparkle particles in background
    for i = 1, 20 do
        local sparkle = Instance.new("Frame")
        sparkle.Size = UDim2.new(0, math.random(4, 10), 0, math.random(4, 10))
        sparkle.Position = UDim2.new(math.random(0, 100) / 100, 0, math.random(0, 100) / 100, 0)
        sparkle.AnchorPoint = Vector2.new(0.5, 0.5)
        sparkle.BackgroundColor3 = color
        sparkle.BorderSizePixel = 0
        sparkle.ZIndex = 99
        sparkle.BackgroundTransparency = 0
        sparkle.Rotation = math.random(0, 360)
        sparkle.Parent = successFrame
        
        local sparkleCorner = Instance.new("UICorner")
        sparkleCorner.CornerRadius = UDim.new(1, 0)
        sparkleCorner.Parent = sparkle
        
        -- Twinkle animation
        task.spawn(function()
            while sparkle.Parent do
                TweenService:Create(sparkle, TweenInfo.new(
                    math.random(5, 10) / 10,
                    Enum.EasingStyle.Quad,
                    Enum.EasingDirection.InOut
                ), {
                    BackgroundTransparency = math.random(0, 50) / 100,
                    Rotation = sparkle.Rotation + math.random(-180, 180)
                }):Play()
                task.wait(math.random(5, 10) / 10)
            end
        end)
    end
    
    local thankYou = Instance.new("TextLabel")
    thankYou.Size = UDim2.new(1, 0, 0.35, 0)
    thankYou.Position = UDim2.new(0, 0, 0.15, 0)
    thankYou.BackgroundTransparency = 1
    thankYou.Text = "🎉 THANK YOU! 🎉"
    thankYou.TextColor3 = Color3.fromRGB(255, 255, 255)
    thankYou.Font = Enum.Font.GothamBold
    thankYou.TextSize = 42
    thankYou.TextTransparency = 1
    thankYou.ZIndex = 101
    thankYou.Parent = successFrame
    
    local thankYouStroke = Instance.new("UIStroke")
    thankYouStroke.Color = color
    thankYouStroke.Thickness = 3
    thankYouStroke.Parent = thankYou
    
    local itemLabel = Instance.new("TextLabel")
    itemLabel.Size = UDim2.new(1, 0, 0.25, 0)
    itemLabel.Position = UDim2.new(0, 0, 0.55, 0)
    itemLabel.BackgroundTransparency = 1
    itemLabel.Text = "✨ " .. itemName .. " received! ✨"
    itemLabel.TextColor3 = color
    itemLabel.Font = Enum.Font.GothamBold
    itemLabel.TextSize = 24
    itemLabel.TextTransparency = 1
    itemLabel.ZIndex = 101
    itemLabel.Parent = successFrame
    
    local subText = Instance.new("TextLabel")
    subText.Size = UDim2.new(1, 0, 0.15, 0)
    subText.Position = UDim2.new(0, 0, 0.78, 0)
    subText.BackgroundTransparency = 1
    subText.Text = "You're awesome! 💖"
    subText.TextColor3 = Color3.fromRGB(255, 255, 255)
    subText.Font = Enum.Font.Gotham
    subText.TextSize = 18
    subText.TextTransparency = 1
    subText.ZIndex = 101
    subText.Parent = successFrame
    
    -- Animate in with rotation and scale
    successFrame.Size = UDim2.new(0, 0, 0, 0)
    successFrame.Rotation = -20
    local expandTween = TweenService:Create(successFrame, TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
        Size = UDim2.new(0, 500, 0, 200),
        BackgroundTransparency = 0,
        Rotation = 0
    })
    
    local textFade1 = TweenService:Create(thankYou, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {TextTransparency = 0})
    local textFade2 = TweenService:Create(itemLabel, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {TextTransparency = 0})
    local textFade3 = TweenService:Create(subText, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {TextTransparency = 0})
    
    expandTween:Play()
    task.wait(0.2)
    textFade1:Play()
    task.wait(0.1)
    textFade2:Play()
    task.wait(0.1)
    textFade3:Play()
    
    -- Extreme pulse effects with color shifts
    for i = 1, 5 do
        local pulseSize = TweenService:Create(successFrame, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = UDim2.new(0, 520, 0, 210)
        })
        local pulseSizeBack = TweenService:Create(successFrame, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            Size = UDim2.new(0, 500, 0, 200)
        })
        local pulseGlow = TweenService:Create(glow, TweenInfo.new(0.25, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), {
            Thickness = 8
        })
        local pulseGlowBack = TweenService:Create(glow, TweenInfo.new(0.25, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), {
            Thickness = 4
        })
        local textPulse = TweenService:Create(thankYou, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            TextSize = 46
        })
        local textPulseBack = TweenService:Create(thankYou, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            TextSize = 42
        })
        
        pulseSize:Play()
        pulseGlow:Play()
        textPulse:Play()
        task.wait(0.25)
        pulseSizeBack:Play()
        pulseGlowBack:Play()
        textPulseBack:Play()
        task.wait(0.25)
    end
    
    -- Hold for a moment
    task.wait(0.5)
    
    -- Animate out with spin
    local shrinkTween = TweenService:Create(successFrame, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.In), {
        Size = UDim2.new(0, 0, 0, 0),
        BackgroundTransparency = 1,
        Rotation = 20
    })
    TweenService:Create(thankYou, fastTween, {TextTransparency = 1}):Play()
    TweenService:Create(itemLabel, fastTween, {TextTransparency = 1}):Play()
    TweenService:Create(subText, fastTween, {TextTransparency = 1}):Play()
    shrinkTween:Play()
    shrinkTween.Completed:Wait()
    successFrame:Destroy()
end

-- Format number with commas
local function formatNumber(num)
    local formatted = tostring(num)
    while true do
        formatted, k = string.gsub(formatted, "^(-?%d+)(%d%d%d)", '%1,%2')
        if k == 0 then break end
    end
    return formatted
end

-- Create the GUI
local function createDonateGui()
    local screenGui = Instance.new("ScreenGui")
    screenGui.Name = "DonateGui"
    screenGui.ResetOnSpawn = false
    screenGui.Enabled = false
    screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    screenGui.DisplayOrder = 1
    
    local shadow = Instance.new("Frame")
    shadow.Name = "Shadow"
    shadow.Size = UDim2.new(1, 0, 1, 0)
    shadow.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
    shadow.BackgroundTransparency = 1
    shadow.BorderSizePixel = 0
    shadow.Parent = screenGui
    
    local mainFrame = Instance.new("Frame")
    mainFrame.Name = "MainFrame"
    mainFrame.Size = UDim2.new(0, 550, 0, 600)
    mainFrame.Position = UDim2.new(0.5, 0, 0.5, 0)
    mainFrame.AnchorPoint = Vector2.new(0.5, 0.5)
    mainFrame.BackgroundColor3 = Color3.fromRGB(40, 40, 50)
    mainFrame.BorderSizePixel = 0
    mainFrame.BackgroundTransparency = 1
    mainFrame.Parent = screenGui
    
    local mainCorner = Instance.new("UICorner")
    mainCorner.CornerRadius = UDim.new(0, 12)
    mainCorner.Parent = mainFrame
    
    local mainStroke = Instance.new("UIStroke")
    mainStroke.Color = Color3.fromRGB(100, 100, 120)
    mainStroke.Thickness = 2
    mainStroke.Transparency = 0.5
    mainStroke.Parent = mainFrame
    
    local title = Instance.new("TextLabel")
    title.Name = "Title"
    title.Size = UDim2.new(1, -40, 0, 60)
    title.Position = UDim2.new(0, 20, 0, 20)
    title.BackgroundTransparency = 1
    title.Text = "💝 Support the Game!"
    title.TextColor3 = Color3.fromRGB(255, 255, 255)
    title.Font = Enum.Font.GothamBold
    title.TextSize = 28
    title.TextXAlignment = Enum.TextXAlignment.Left
    title.TextTransparency = 1
    title.Parent = mainFrame
    
    local subtitle = Instance.new("TextLabel")
    subtitle.Name = "Subtitle"
    subtitle.Size = UDim2.new(1, -40, 0, 30)
    subtitle.Position = UDim2.new(0, 20, 0, 70)
    subtitle.BackgroundTransparency = 1
    subtitle.Text = "Thank you for supporting development!"
    subtitle.TextColor3 = Color3.fromRGB(200, 200, 200)
    subtitle.Font = Enum.Font.Gotham
    subtitle.TextSize = 16
    subtitle.TextXAlignment = Enum.TextXAlignment.Left
    subtitle.TextTransparency = 1
    subtitle.Parent = mainFrame
    
    local closeBtn = Instance.new("TextButton")
    closeBtn.Name = "CloseButton"
    closeBtn.Size = UDim2.new(0, 40, 0, 40)
    closeBtn.Position = UDim2.new(1, -50, 0, 15)
    closeBtn.BackgroundColor3 = Color3.fromRGB(60, 60, 70)
    closeBtn.Text = "✕"
    closeBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
    closeBtn.Font = Enum.Font.GothamBold
    closeBtn.TextSize = 20
    closeBtn.AutoButtonColor = false
    closeBtn.BackgroundTransparency = 1
    closeBtn.TextTransparency = 1
    closeBtn.Parent = mainFrame
    
    local closeBtnCorner = Instance.new("UICorner")
    closeBtnCorner.CornerRadius = UDim.new(0, 8)
    closeBtnCorner.Parent = closeBtn
    
    closeBtn.MouseEnter:Connect(function()
        TweenService:Create(closeBtn, fastTween, {BackgroundColor3 = Color3.fromRGB(200, 60, 60)}):Play()
    end)
    
    closeBtn.MouseLeave:Connect(function()
        TweenService:Create(closeBtn, fastTween, {BackgroundColor3 = Color3.fromRGB(60, 60, 70)}):Play()
    end)
    
    closeBtn.MouseButton1Click:Connect(function()
        TweenService:Create(shadow, fastTween, {BackgroundTransparency = 1}):Play()
        TweenService:Create(mainFrame, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.In), {
            Size = UDim2.new(0, 0, 0, 0),
            BackgroundTransparency = 1
        }):Play()
        TweenService:Create(title, fastTween, {TextTransparency = 1}):Play()
        TweenService:Create(subtitle, fastTween, {TextTransparency = 1}):Play()
        TweenService:Create(closeBtn, fastTween, {BackgroundTransparency = 1, TextTransparency = 1}):Play()
        
        for _, item in pairs(mainFrame.Container:GetChildren()) do
            if item:IsA("Frame") then
                TweenService:Create(item, fastTween, {BackgroundTransparency = 1}):Play()
                for _, child in pairs(item:GetChildren()) do
                    if child:IsA("TextLabel") or child:IsA("TextButton") then
                        TweenService:Create(child, fastTween, {TextTransparency = 1, BackgroundTransparency = 1}):Play()
                    end
                end
            end
        end
        
        -- Fade out stats and leaderboard
        if mainFrame:FindFirstChild("StatsPanel") then
            TweenService:Create(mainFrame.StatsPanel, fastTween, {BackgroundTransparency = 1}):Play()
            for _, child in pairs(mainFrame.StatsPanel:GetDescendants()) do
                if child:IsA("TextLabel") or child:IsA("Frame") then
                    TweenService:Create(child, fastTween, {BackgroundTransparency = 1}):Play()
                    if child:IsA("TextLabel") then
                        TweenService:Create(child, fastTween, {TextTransparency = 1}):Play()
                    end
                end
            end
        end
        
        if mainFrame:FindFirstChild("LeaderboardPanel") then
            TweenService:Create(mainFrame.LeaderboardPanel, fastTween, {BackgroundTransparency = 1}):Play()
            for _, child in pairs(mainFrame.LeaderboardPanel:GetDescendants()) do
                if child:IsA("TextLabel") or child:IsA("Frame") then
                    TweenService:Create(child, fastTween, {BackgroundTransparency = 1}):Play()
                    if child:IsA("TextLabel") then
                        TweenService:Create(child, fastTween, {TextTransparency = 1}):Play()
                    end
                end
            end
        end
        
        task.wait(0.3)
        screenGui.Enabled = false
    end)
    
    local container = Instance.new("Frame")
    container.Name = "Container"
    container.Size = UDim2.new(1, -40, 0, 300)
    container.Position = UDim2.new(0, 20, 0, 110)
    container.BackgroundTransparency = 1
    container.Parent = mainFrame
    
    local gridLayout = Instance.new("UIGridLayout")
    gridLayout.CellSize = UDim2.new(0, 240, 0, 140)
    gridLayout.CellPadding = UDim2.new(0, 15, 0, 15)
    gridLayout.SortOrder = Enum.SortOrder.LayoutOrder
    gridLayout.Parent = container
    
    for i, item in ipairs(donationItems) do
        local itemFrame = Instance.new("Frame")
        itemFrame.Name = "Item" .. i
        itemFrame.BackgroundColor3 = Color3.fromRGB(50, 50, 60)
        itemFrame.BorderSizePixel = 0
        itemFrame.LayoutOrder = i
        itemFrame.BackgroundTransparency = 1
        itemFrame.Parent = container
        
        local itemCorner = Instance.new("UICorner")
        itemCorner.CornerRadius = UDim.new(0, 10)
        itemCorner.Parent = itemFrame
        
        local itemStroke = Instance.new("UIStroke")
        itemStroke.Color = item.color
        itemStroke.Thickness = 2
        itemStroke.Transparency = 0.7
        itemStroke.Parent = itemFrame
        
        local accent = Instance.new("Frame")
        accent.Name = "Accent"
        accent.Size = UDim2.new(1, 0, 0, 4)
        accent.BackgroundColor3 = item.color
        accent.BorderSizePixel = 0
        accent.BackgroundTransparency = 1
        accent.Parent = itemFrame
        
        local accentCorner = Instance.new("UICorner")
        accentCorner.CornerRadius = UDim.new(0, 10)
        accentCorner.Parent = accent
        
        local emoji = Instance.new("TextLabel")
        emoji.Size = UDim2.new(0, 40, 0, 40)
        emoji.Position = UDim2.new(1, -50, 0, 10)
        emoji.BackgroundTransparency = 1
        emoji.Text = item.emoji
        emoji.TextSize = 30
        emoji.TextTransparency = 1
        emoji.Parent = itemFrame
        
        local itemName = Instance.new("TextLabel")
        itemName.Size = UDim2.new(1, -60, 0, 30)
        itemName.Position = UDim2.new(0, 10, 0, 15)
        itemName.BackgroundTransparency = 1
        itemName.Text = item.name
        itemName.TextColor3 = Color3.fromRGB(255, 255, 255)
        itemName.Font = Enum.Font.GothamBold
        itemName.TextSize = 18
        itemName.TextXAlignment = Enum.TextXAlignment.Left
        itemName.TextTransparency = 1
        itemName.Parent = itemFrame
        
        local priceLabel = Instance.new("TextLabel")
        priceLabel.Size = UDim2.new(1, -20, 0, 25)
        priceLabel.Position = UDim2.new(0, 10, 0, 45)
        priceLabel.BackgroundTransparency = 1
        priceLabel.Text = "R$" .. item.price
        priceLabel.TextColor3 = item.color
        priceLabel.Font = Enum.Font.GothamBold
        priceLabel.TextSize = 24
        priceLabel.TextXAlignment = Enum.TextXAlignment.Left
        priceLabel.TextTransparency = 1
        priceLabel.Parent = itemFrame
        
        local buyBtn = Instance.new("TextButton")
        buyBtn.Name = "BuyButton"
        buyBtn.Size = UDim2.new(1, -20, 0, 35)
        buyBtn.Position = UDim2.new(0, 10, 1, -45)
        buyBtn.BackgroundColor3 = item.color
        buyBtn.Text = "Donate Now"
        buyBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
        buyBtn.Font = Enum.Font.GothamBold
        buyBtn.TextSize = 16
        buyBtn.AutoButtonColor = false
        buyBtn.BackgroundTransparency = 1
        buyBtn.TextTransparency = 1
        buyBtn.Parent = itemFrame
        
        local buyBtnCorner = Instance.new("UICorner")
        buyBtnCorner.CornerRadius = UDim.new(0, 8)
        buyBtnCorner.Parent = buyBtn
        
        buyBtn.MouseEnter:Connect(function()
            TweenService:Create(buyBtn, fastTween, {
                Size = UDim2.new(1, -16, 0, 38),
                Position = UDim2.new(0, 8, 1, -47)
            }):Play()
            TweenService:Create(itemStroke, fastTween, {Transparency = 0.3}):Play()
        end)
        
        buyBtn.MouseLeave:Connect(function()
            TweenService:Create(buyBtn, fastTween, {
                Size = UDim2.new(1, -20, 0, 35),
                Position = UDim2.new(0, 10, 1, -45)
            }):Play()
            TweenService:Create(itemStroke, fastTween, {Transparency = 0.7}):Play()
        end)
        
        buyBtn.MouseButton1Click:Connect(function()
            if item.productId and item.productId > 0 then
                local originalSize = buyBtn.Size
                local originalPos = buyBtn.Position
                TweenService:Create(buyBtn, TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                    Size = UDim2.new(1, -24, 0, 32),
                    Position = UDim2.new(0, 12, 1, -44)
                }):Play()
                task.wait(0.1)
                TweenService:Create(buyBtn, TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                    Size = originalSize,
                    Position = originalPos
                }):Play()
                
                MarketplaceService:PromptProductPurchase(player, item.productId)
            else
                warn("Product ID not set for: " .. item.name)
            end
        end)
    end
    
    -- YOUR STATS PANEL
    local statsPanel = Instance.new("Frame")
    statsPanel.Name = "StatsPanel"
    statsPanel.Size = UDim2.new(1, -40, 0, 70)
    statsPanel.Position = UDim2.new(0, 20, 0, 420)
    statsPanel.BackgroundColor3 = Color3.fromRGB(50, 50, 60)
    statsPanel.BorderSizePixel = 0
    statsPanel.BackgroundTransparency = 1
    statsPanel.Parent = mainFrame
    
    local statsCorner = Instance.new("UICorner")
    statsCorner.CornerRadius = UDim.new(0, 10)
    statsCorner.Parent = statsPanel
    
    local statsStroke = Instance.new("UIStroke")
    statsStroke.Color = Color3.fromRGB(255, 200, 50)
    statsStroke.Thickness = 2
    statsStroke.Transparency = 0.7
    statsStroke.Parent = statsPanel
    
    local statsTitle = Instance.new("TextLabel")
    statsTitle.Name = "StatsTitle"
    statsTitle.Size = UDim2.new(1, -20, 0, 25)
    statsTitle.Position = UDim2.new(0, 10, 0, 5)
    statsTitle.BackgroundTransparency = 1
    statsTitle.Text = "⭐ Your Donations"
    statsTitle.TextColor3 = Color3.fromRGB(255, 200, 50)
    statsTitle.Font = Enum.Font.GothamBold
    statsTitle.TextSize = 16
    statsTitle.TextXAlignment = Enum.TextXAlignment.Left
    statsTitle.TextTransparency = 1
    statsTitle.Parent = statsPanel
    
    local statsAmount = Instance.new("TextLabel")
    statsAmount.Name = "StatsAmount"
    statsAmount.Size = UDim2.new(1, -20, 0, 35)
    statsAmount.Position = UDim2.new(0, 10, 0, 30)
    statsAmount.BackgroundTransparency = 1
    statsAmount.Text = "R$0"
    statsAmount.TextColor3 = Color3.fromRGB(255, 255, 255)
    statsAmount.Font = Enum.Font.GothamBold
    statsAmount.TextSize = 28
    statsAmount.TextXAlignment = Enum.TextXAlignment.Left
    statsAmount.TextTransparency = 1
    statsAmount.Parent = statsPanel
    
    -- LEADERBOARD PANEL
    local leaderboardPanel = Instance.new("Frame")
    leaderboardPanel.Name = "LeaderboardPanel"
    leaderboardPanel.Size = UDim2.new(1, -40, 0, 85)
    leaderboardPanel.Position = UDim2.new(0, 20, 0, 500)
    leaderboardPanel.BackgroundColor3 = Color3.fromRGB(50, 50, 60)
    leaderboardPanel.BorderSizePixel = 0
    leaderboardPanel.BackgroundTransparency = 1
    leaderboardPanel.Parent = mainFrame
    
    local lbCorner = Instance.new("UICorner")
    lbCorner.CornerRadius = UDim.new(0, 10)
    lbCorner.Parent = leaderboardPanel
    
    local lbStroke = Instance.new("UIStroke")
    lbStroke.Color = Color3.fromRGB(100, 150, 255)
    lbStroke.Thickness = 2
    lbStroke.Transparency = 0.7
    lbStroke.Parent = leaderboardPanel
    
    local lbTitle = Instance.new("TextLabel")
    lbTitle.Name = "LBTitle"
    lbTitle.Size = UDim2.new(1, -20, 0, 25)
    lbTitle.Position = UDim2.new(0, 10, 0, 5)
    lbTitle.BackgroundTransparency = 1
    lbTitle.Text = "🏆 Top Donors"
    lbTitle.TextColor3 = Color3.fromRGB(100, 150, 255)
    lbTitle.Font = Enum.Font.GothamBold
    lbTitle.TextSize = 16
    lbTitle.TextXAlignment = Enum.TextXAlignment.Left
    lbTitle.TextTransparency = 1
    lbTitle.Parent = leaderboardPanel
    
    local lbContainer = Instance.new("Frame")
    lbContainer.Name = "LBContainer"
    lbContainer.Size = UDim2.new(1, -20, 1, -35)
    lbContainer.Position = UDim2.new(0, 10, 0, 30)
    lbContainer.BackgroundTransparency = 1
    lbContainer.Parent = leaderboardPanel
    
    -- Create 3 leaderboard slots
    for i = 1, 3 do
        local slot = Instance.new("TextLabel")
        slot.Name = "Slot" .. i
        slot.Size = UDim2.new(0.33, -5, 1, 0)
        slot.Position = UDim2.new((i-1) * 0.33, 0, 0, 0)
        slot.BackgroundTransparency = 1
        slot.Text = i .. ". Loading..."
        slot.TextColor3 = Color3.fromRGB(200, 200, 200)
        slot.Font = Enum.Font.Gotham
        slot.TextSize = 12
        slot.TextXAlignment = Enum.TextXAlignment.Left
        slot.TextYAlignment = Enum.TextYAlignment.Top
        slot.TextWrapped = true
        slot.TextTransparency = 1
        slot.Parent = lbContainer
    end
    
    -- Function to update stats
    local function updateStats()
        local success, data = pcall(function()
            return getDonationData:InvokeServer()
        end)
        
        if success and data then
            -- Update player stats
            statsAmount.Text = "R$" .. formatNumber(data.playerTotal or 0)
            
            -- Update leaderboard
            if data.leaderboard then
                for i = 1, 3 do
                    local slot = lbContainer:FindFirstChild("Slot" .. i)
                    if slot then
                        if data.leaderboard[i] then
                            local lb = data.leaderboard[i]
                            slot.Text = i .. ". " .. lb.name .. "\nR$" .. formatNumber(lb.amount)
                        else
                            slot.Text = i .. ". ---"
                        end
                    end
                end
            end
        end
    end
    
    -- Update stats when GUI opens
    screenGui.Changed:Connect(function(prop)
        if prop == "Enabled" and screenGui.Enabled then
            mainFrame.Size = UDim2.new(0, 0, 0, 0)
            mainFrame.BackgroundTransparency = 1
            shadow.BackgroundTransparency = 1
            title.TextTransparency = 1
            subtitle.TextTransparency = 1
            closeBtn.BackgroundTransparency = 1
            closeBtn.TextTransparency = 1
            
            -- Update donation data
            updateStats()
            
            TweenService:Create(shadow, slowTween, {BackgroundTransparency = 0.5}):Play()
            TweenService:Create(mainFrame, tweenInfo, {
                Size = UDim2.new(0, 550, 0, 600),
                BackgroundTransparency = 0
            }):Play()
            
            task.wait(0.15)
            TweenService:Create(title, fastTween, {TextTransparency = 0}):Play()
            TweenService:Create(subtitle, fastTween, {TextTransparency = 0}):Play()
            TweenService:Create(closeBtn, fastTween, {BackgroundTransparency = 0, TextTransparency = 0}):Play()
            
            for i, item in pairs(container:GetChildren()) do
                if item:IsA("Frame") then
                    task.wait(0.05)
                    TweenService:Create(item, tweenInfo, {BackgroundTransparency = 0}):Play()
                    TweenService:Create(item.Accent, tweenInfo, {BackgroundTransparency = 0}):Play()
                    TweenService:Create(item.BuyButton, fastTween, {BackgroundTransparency = 0, TextTransparency = 0}):Play()
                    for _, child in pairs(item:GetChildren()) do
                        if child:IsA("TextLabel") then
                            TweenService:Create(child, fastTween, {TextTransparency = 0}):Play()
                        end
                    end
                end
            end
            
            -- Animate stats panel
            task.wait(0.1)
            TweenService:Create(statsPanel, tweenInfo, {BackgroundTransparency = 0}):Play()
            TweenService:Create(statsTitle, fastTween, {TextTransparency = 0}):Play()
            TweenService:Create(statsAmount, fastTween, {TextTransparency = 0}):Play()
            
            -- Animate leaderboard
            task.wait(0.05)
            TweenService:Create(leaderboardPanel, tweenInfo, {BackgroundTransparency = 0}):Play()
            TweenService:Create(lbTitle, fastTween, {TextTransparency = 0}):Play()
            for _, slot in pairs(lbContainer:GetChildren()) do
                if slot:IsA("TextLabel") then
                    TweenService:Create(slot, fastTween, {TextTransparency = 0}):Play()
                end
            end
        end
    end)
    
    screenGui.Parent = playerGui
    return screenGui, statsAmount
end

-- Create the GUI
local donateGui, statsLabel = createDonateGui()

-- Handle chat commands
player.Chatted:Connect(function(message)
    if message:lower() == "!donate" then
        donateGui.Enabled = not donateGui.Enabled
    end
end)

-- Close when clicking shadow
donateGui.Shadow.InputBegan:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1 then
        local closeBtn = donateGui.MainFrame.CloseButton
        closeBtn.MouseButton1Click:Fire()
    end
end)

-- Listen for successful purchases
MarketplaceService.PromptProductPurchaseFinished:Connect(function(userId, productId, isPurchased)
    if userId == player.UserId and isPurchased then
        for _, item in ipairs(donationItems) do
            if item.productId == productId then
                task.spawn(function()
                    createConfetti(donateGui.Shadow, item.color)
                end)
                task.spawn(function()
                    showSuccessMessage(donateGui.Shadow, item.name, item.color)
                end)
                
                -- Update stats after purchase
                task.wait(1)
                local success, data = pcall(function()
                    return getDonationData:InvokeServer()
                end)
                if success and data then
                    statsLabel.Text = "R$" .. formatNumber(data.playerTotal or 0)
                    
                    -- Pulse animation on stats
                    TweenService:Create(statsLabel, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                        TextSize = 32
                    }):Play()
                    task.wait(0.2)
                    TweenService:Create(statsLabel, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                        TextSize = 28
                    }):Play()
                end
                break
            end
        end
    end
end)

-- Listen for leaderboard updates
updateLeaderboard.OnClientEvent:Connect(function(data)
    if donateGui.Enabled then
        local lbContainer = donateGui.MainFrame.LeaderboardPanel.LBContainer
        if data.leaderboard then
            for i = 1, 3 do
                local slot = lbContainer:FindFirstChild("Slot" .. i)
                if slot then
                    if data.leaderboard[i] then
                        local lb = data.leaderboard[i]
                        slot.Text = i .. ". " .. lb.name .. "\nR$" .. formatNumber(lb.amount)
                    else
                        slot.Text = i .. ". ---"
                    end
                end
            end
        end
    end
end)

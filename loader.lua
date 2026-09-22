--!strict

local BASE = "https://raw.githubusercontent.com/cookieys/cookies.github.io/refs/heads/main/"

local ok, registry = pcall(function()
	return loadstring(game:HttpGet(BASE .. "list.lua"))() :: {[number]: string}
end)

if not ok or not registry then
	return warn("[Loader] Failed to fetch game registry")
end

local target = registry[game.GameId]
if not target then
	return warn("[Loader] Unsupported game:", game.GameId)
end

local success, err = pcall(loadstring, game:HttpGet(target))
if not success then
	warn("[Loader] Script error:", err)
end
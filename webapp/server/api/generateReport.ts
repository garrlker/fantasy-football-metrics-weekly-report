import { $ } from "bun";

const cmdBase = `docker exec -it fantasy-football-metrics-weekly-report_app_1 python main.py `
const platformFlag = `-f sleeper `
const leagueFlag = leagueId => `-l ${leagueId}`
const weekFlag = week => `-w ${week}`

export default defineEventHandler(async (event) => {
  await $`${cmdBase}${platformFlag}${leagueFlag("1049710389472133120")}${weekFlag("6")}`;
  return {
    hello: 'world'
  }
})
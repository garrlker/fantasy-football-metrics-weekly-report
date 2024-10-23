import { $ } from "bun";

const cmdBase = `docker exec -i fantasy-football-metrics-weekly-report-app-1 python main.py -d`
const platformFlag = `-f sleeper `
const leagueFlag = leagueId => `-l ${leagueId}`
const weekFlag = week => `-w ${week}`

const cmdArray = cmdBase.split(" ");
cmdArray.push(...cmdBase.split(" "))
cmdArray.push(...platformFlag.split(" "))
cmdArray.push(...leagueFlag("1049710389472133120").split(" "))
cmdArray.push(...weekFlag(7).split(" "))
export default defineEventHandler(async (event) => {
  // await $`${cmdBase}${platformFlag}${leagueFlag("1049710389472133120")}${weekFlag("6")}`;

  const proc = Bun.spawn(cmdArray);

  const output = await new Response(proc.stdout).text();

  return {
    hello: output
  }
})
import logging
import time

from smarts.core.smarts import SMARTS
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.core.agent import AgentSpec, Agent
from smarts.core.sumo_traffic_simulation import SumoTrafficSimulation
from smarts.core.scenario import Scenario
from envision.client import Client as Envision

from examples import default_argument_parser


logging.basicConfig(level=logging.INFO)


class KeepLaneAgent(Agent):
    def act(self, obs):
        return "keep_lane"


def main(scenarios, headless, seed):
    scenarios_iterator = Scenario.scenario_variations(scenarios, [])
    first_time = True
    smarts = None

    for _ in scenarios:
        scenario = next(scenarios_iterator)
        agent_missions = scenario.discover_missions_of_traffic_histories()

        for agent_id, mission in agent_missions.items():
            # if agent_id not in set(["10","11"]):
            #     continue
            print(f"agent id: {agent_id}")
            scenario.set_ego_missions({agent_id: mission})

            agent_spec = AgentSpec(
                interface=AgentInterface.from_type(
                    AgentType.Laner, max_episode_steps=None
                ),
                agent_builder=KeepLaneAgent,
            )
            agent = agent_spec.build_agent()

            if first_time:
                print("smarts initial setup")
                start = time.time()
                smarts = SMARTS(
                    agent_interfaces={agent_id: agent_spec.interface},
                    traffic_sim=SumoTrafficSimulation(headless=True, auto_start=True),
                    envision=Envision(),
                )
                first_time = False
                end = time.time()
                print(f"smarts done setup: {end - start}\n")
            else:
                print("smarts setup")
                start = time.time()
                smarts.switch_ego_agent({agent_id: agent_spec.interface})
                # smarts = SMARTS(
                #     agent_interfaces={agent_id: agent_spec.interface},
                #     traffic_sim=SumoTrafficSimulation(headless=True, auto_start=True),
                #     envision=Envision(),
                # )
                end = time.time()
                print(f"smarts done setup: {end - start}\n")

            print("smarts reset")
            start = time.time()
            observations = smarts.reset(scenario)
            end = time.time()
            print(f"smarts done reset: {end - start}\n")

            print(agent_id)
            dones = {agent_id: False}
            while not dones[agent_id]:
                agent_obs = observations[agent_id]
                agent_action = agent.act(agent_obs)

                observations, rewards, dones, infos = smarts.step(
                    {agent_id: agent_action}
                )

    smarts.destroy()


if __name__ == "__main__":
    parser = default_argument_parser("history-vehicles-replacement-example")
    args = parser.parse_args()

    main(
        scenarios=args.scenarios, headless=args.headless, seed=args.seed,
    )

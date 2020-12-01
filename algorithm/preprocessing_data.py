import numpy as np
import pandas as pd
import datetime
import json
from datetime import date, timedelta
import time
import copy
import math
from itertools import islice
import random


class CsvPreProcessing:
    # points params
    teacher_has_chaining_subject = 2
    teacher_has_full_day = 20
    student_has_chaining_subject = 1
    student_has_full_day = 20
    student_stays_in_same_room = 2
    student_stays_in_same_room_for_same_subject = 100
    week_ratio_respected = 200
    first_hoc_vs_other = 100
    specialisation_same_hour = 50
    student_has_same_subject = 40

    # todo: add intro subjects in first weeks points and add it to the fitness function

    def __init__(self):
        df_docenten = pd.read_csv('./data_sets/docenten.csv', sep=',')
        df_docenten = df_docenten.replace(np.nan, '', regex=True)
        df_docenten["niet_beschikbare_dagen"] = df_docenten["niet_beschikbare_dagen"].str.split("|", expand=False)
        df_lokalen = pd.read_csv('./data_sets/lokalen.csv', sep=',')
        df_lokalen = df_lokalen.replace(np.nan, '', regex=True)
        df_lokalen["Speciale_voorziening"] = df_lokalen["Speciale_voorziening"].str.split("|", expand=False)
        df_subjects = pd.read_csv('./data_sets/semester1.csv', sep=',')
        df_subjects = df_subjects.replace(np.nan, '', regex=True)
        df_subjects["Docenten_HOC"] = df_subjects["Docenten_HOC"].str.split("|", expand=False)
        df_subjects["Docenten_WEC"] = df_subjects["Docenten_WEC"].str.split("|", expand=False)
        df_subjects["Docenten_Afstandsonderwijs"] = df_subjects["Docenten_Afstandsonderwijs"].str.split("|",
                                                                                                        expand=False)
        df_subjects["opleiding"] = df_subjects["opleiding"].str.split("|", expand=False)
        df_subjects["lesblok"] = df_subjects["lesblok"].str.split("|", expand=False)
        df_subjects["ratio_uren_HOC_vs_WEC_vs_afstand"] = df_subjects["ratio_uren_HOC_vs_WEC_vs_afstand"].str.split("|",
                                                                                                                    expand=False)
        df_exclusion_dates = pd.read_csv('./data_sets/exclusion_dates.csv', sep=',')

        # parameters
        start_dt = date(2020, 9, 21)
        end_dt = date(2021, 1, 8)
        morning_slots = {'09:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''},
                         '10:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''},
                         '11:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''},
                         '12:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''}}
        afternoon_slots = {'14:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''},
                           '15:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''},
                           '16:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''},
                           '17:00': {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '', 'colleagues': [], 'amount_of_students': ''}}
        day_of_week_half_day = 1

        school_days = CsvPreProcessing.get_school_days(start_dt, end_dt, df_exclusion_dates.iloc[:, 0].values.tolist())
        days_with_slots = copy.deepcopy(CsvPreProcessing.add_slots_to_school_days(
            school_days, morning_slots, afternoon_slots, day_of_week_half_day))

        # create a dict with teachers possible working days
        dict_docenten = dict([(i, [a, b, c, d, e, f]) for i, a, b, c, d, e, f in
                              zip(df_docenten.naam, df_docenten.maandag, df_docenten.dinsdag, df_docenten.woensdag,
                                  df_docenten.donderdag, df_docenten.vrijdag, df_docenten.niet_beschikbare_dagen)])

        # create a dict with classrooms capacity and infrastructure
        records_lokalen = df_lokalen.to_dict('records')
        dict_lokalen = {}
        for record in records_lokalen:
            for equipment in record['Speciale_voorziening']:
                if equipment not in dict_lokalen.keys():
                    dict_lokalen[equipment] = []
                dict_lokalen[equipment].append(record)

        # create a dict with subjects
        dict_subjects = df_subjects.to_dict('records')

        # create subjects weekly overview dict
        week_numbers_days = CsvPreProcessing.get_weeknumbers_with_days(school_days)
        dict_week_overview = {'weeks': {}, 'ratio': ''}
        week_overview = {'first_hoc': True, 'ratio_respected': True, 'week_scheduled': False,
                                                 'HOC': 0, 'WEC': 0, 'afstandsonderwijs': 0}
        for week in week_numbers_days.keys():
            dict_week_overview['weeks'][week] = copy.deepcopy(week_overview)

        dict_overview_subjects = {}
        for subject in dict_subjects:
            dict_overview_subjects[f"{subject['Naam']}%{'%'.join(subject['opleiding'])}"] = copy.deepcopy(dict_week_overview)
            dict_overview_subjects[f"{subject['Naam']}%{'%'.join(subject['opleiding'])}"]['ratio'] = subject['ratio_uren_HOC_vs_WEC_vs_afstand']

        teachers_with_days = self.add_days_to_teachers(dict_docenten, days_with_slots, morning_slots, afternoon_slots)

        # fitness functionality

        # solution params
        population = 200
        solutions_drop_ratio = 0.3
        new_generations_drop_ratio = 0.5
        # how many times he tries to create more generations
        generations = 1000
        children = 30
        number_of_teachers_to_cross = 10
        mutations = 16
        max_amount_solutions = 250

        solutions = []

        # generating the initial parents
        for x in range(population):
            teachers_with_days_copy = copy.deepcopy(teachers_with_days)
            dict_tracking_days_slots_teachers_groups = copy.deepcopy(days_with_slots)
            not_fully_scheduled_solution = CsvPreProcessing.building_solution(days_with_slots, school_days, dict_subjects,
                                                                             teachers_with_days_copy, dict_lokalen,
                                                                              dict_tracking_days_slots_teachers_groups)
            if not not_fully_scheduled_solution:
                solution_points = CsvPreProcessing.fitness_function(teachers_with_days_copy, days_with_slots, copy.deepcopy(dict_overview_subjects))
                solutions.append({'score': solution_points, 'solution': teachers_with_days_copy,
                                  'usage_tracker': dict_tracking_days_slots_teachers_groups})
        print(len(solutions))
        print(solutions[0]['score'])

        for solution in solutions:
            CsvPreProcessing.check_solution(solution)
            CsvPreProcessing.check_control_dict(solution)
        # creating the children
        for x in range(generations):
            solutions = CsvPreProcessing.cross_over_generations(solutions, children, number_of_teachers_to_cross, dict_lokalen,
                                                    days_with_slots, dict_overview_subjects, solutions_drop_ratio, new_generations_drop_ratio, mutations, x)
            solutions = solutions[:max_amount_solutions]
            # print(len(solutions))

    @staticmethod
    def cross_over_generations(solutions, children, number_of_teachers_to_cross, dict_lokalen, days_with_slots,
                               dict_overview_subjects, solutions_drop_ratio, new_generations_drop_ratio, mutations, generation_number):
        strongest_parents = CsvPreProcessing.retrieve_top_solutions_for_next_gen(solutions, solutions_drop_ratio)

        new_generations = []
        amount_solutions = len(strongest_parents)
        while children > 0:
            solution1 = copy.deepcopy(strongest_parents[random.randint(0, amount_solutions - 1)])
            # CsvPreProcessing.check_solution(solution1)
            # CsvPreProcessing.check_control_dict(solution1)
            solution2 = copy.deepcopy(strongest_parents[random.randint(0, amount_solutions - 1)])
            # CsvPreProcessing.check_control_dict(solution2)
            # CsvPreProcessing.check_solution(solution2)
            CsvPreProcessing.cross_over(solution1, solution2, number_of_teachers_to_cross, dict_lokalen, mutations)
            # CsvPreProcessing.check_solution(solution1)
            # CsvPreProcessing.check_solution(solution2)
            # CsvPreProcessing.check_control_dict(solution1)
            # CsvPreProcessing.check_control_dict(solution2)
            solution1['score'] = CsvPreProcessing.fitness_function(solution1['solution'], days_with_slots,
                                                                copy.deepcopy(dict_overview_subjects))
            # print(f"score solution 1: {solution1['score']}")
            solution2['score'] = CsvPreProcessing.fitness_function(solution2['solution'], days_with_slots,
                                                                copy.deepcopy(dict_overview_subjects))
            # print(f"score solution 2: {solution2['score']}")
            new_generations.append(solution1)
            new_generations.append(solution2)
            children -= 2

        # new_generations.sort(key=lambda x: x.get('score'), reverse=True)
        new_generations = CsvPreProcessing.retrieve_top_solutions_for_next_gen(new_generations, new_generations_drop_ratio)
        print(f"generation {generation_number} top score : {new_generations[0]['score']}")
        return solutions + new_generations


    @staticmethod
    def check_control_dict(solution):
        # print(solution['usage_tracker'])
        amount_of_subjects = 0
        amount_of_locations = 0
        amount_of_colleagues = 0
        amount_of_groups = 0
        for day in solution['usage_tracker'].keys():
            for slot in solution['usage_tracker'][day].keys():
                amount_of_subjects += len(solution['usage_tracker'][day][slot]['subject'].split(','))
                amount_of_locations += len(solution['usage_tracker'][day][slot]['locations'])
                amount_of_colleagues += len(solution['usage_tracker'][day][slot]['colleagues'])
                amount_of_groups += len(solution['usage_tracker'][day][slot]['groups'])
        print(f'subject: {amount_of_subjects} - locations: {amount_of_locations} - groups: {amount_of_groups} - colleagues: {amount_of_colleagues}')

    @staticmethod
    def check_solution(solution):
        amount_slots_booked = 0
        amount_locations_booked = 0
        amount_groups_booked = 0
        ruben_slots = 0
        subject_dict = {}
        for teacher in solution['solution'].keys():
            for day in solution['solution'][teacher].keys():
                for slot in solution['solution'][teacher][day].keys():
                    if teacher == 'Dejonckheere Ruben':
                        ruben_slots += 1
                    if solution['solution'][teacher][day][slot]['subject']:
                        amount_slots_booked += 1
                        amount_locations_booked += len(solution['solution'][teacher][day][slot]['locations'])
                        amount_groups_booked += len(solution['solution'][teacher][day][slot]['groups'])
                        subject = solution['solution'][teacher][day][slot]['subject']
                        if subject not in subject_dict.keys():
                            subject_dict[subject] = 0
                        subject_dict[subject] += 1
        print(f'solution - slots booked: {amount_slots_booked} - locations booked: {amount_locations_booked} - groups booked: {amount_groups_booked} - ruben slots: {ruben_slots}')
        control_string = ""
        # for subject in sorted(subject_dict.keys()):
        #     control_string += f'{subject}: {subject_dict[subject]} '
        # print(control_string)

    @staticmethod
    def cross_over(solution1, solution2, number_of_teachers_to_cross, dict_lokalen, mutations):
        # changes = 0
        # changes_before_reset = 0
        # changes_find_new_slot1 = 0
        teachers = list(solution1['solution'].keys())
        # for x in range(number_of_teachers_to_cross):
        for x in range(random.randint(1, number_of_teachers_to_cross)):
            teacher_to_cross_over = teachers[random.randint(0, len(teachers) - 1)]
            days = list(solution1['solution'][teacher_to_cross_over].keys())
            start_replace = random.randint(0, len(days) - 1)
            end_replace = random.randint(start_replace, len(days))

            while start_replace < end_replace:
                day_replace = days[start_replace]
                for slot_time, slot_value in solution1['solution'][teacher_to_cross_over][days[start_replace]].items():
                    # print(teacher_to_cross_over)
                    # print(days[start_replace])
                    # print(slot_time)
                    # print(slot_value)
                    # print(solution1['solution'][teacher_to_cross_over][days[start_replace]])
                    # print(solution2['solution'][teacher_to_cross_over][days[start_replace]])

                    # between_result_1 = copy.deepcopy(solution1['solution'][teacher_to_cross_over])
                    # between_result_2 = copy.deepcopy(solution2['solution'][teacher_to_cross_over])

                    temp_slot1 = copy.deepcopy(solution1['solution'][teacher_to_cross_over][days[start_replace]][slot_time])
                    temp_slot2 = copy.deepcopy(solution2['solution'][teacher_to_cross_over][days[start_replace]][slot_time])

                    # if (temp_slot1['subject'] or temp_slot2['subject']) and not (temp_slot2['subject'] == temp_slot1['subject'] and temp_slot2['type'] == temp_slot1['type'] and sorted(temp_slot1['groups']) == sorted(temp_slot2['groups'])) and temp_slot2['subject'] == 'Desktop OS' and temp_slot1['subject'] == 'Programming Essentials 1':
                    if (temp_slot1['subject'] or temp_slot2['subject']) and not (temp_slot2['subject'] == temp_slot1['subject'] and temp_slot2['type'] == temp_slot1['type'] and sorted(temp_slot1['groups']) == sorted(temp_slot2['groups'])):
                        between_results1 = {}
                        between_results2 = {}
                        for colleague in temp_slot2['colleagues']:
                            between_results1[colleague] = copy.deepcopy(solution1['solution'][colleague])
                            between_results2[colleague] = copy.deepcopy(solution2['solution'][colleague])
                        between_results1[teacher_to_cross_over] = copy.deepcopy(solution1['solution'][teacher_to_cross_over])
                        for colleague in temp_slot1['colleagues']:
                            if colleague not in between_results1:
                                between_results1[colleague] = copy.deepcopy(solution1['solution'][colleague])
                            if colleague not in between_results2:
                                between_results2[colleague] = copy.deepcopy(solution2['solution'][colleague])
                        between_results2[teacher_to_cross_over] = copy.deepcopy(solution2['solution'][teacher_to_cross_over])

                        colleagues_ok = False

                        # check group
                        group_ok = False
                        if sorted(temp_slot1['groups']) == sorted(temp_slot2['groups']):
                            group_ok = True
                        else:
                            if CsvPreProcessing.check_group_available(slot_time, temp_slot1, solution2, day_replace) and \
                                    CsvPreProcessing.check_group_available(slot_time, temp_slot2, solution1, day_replace):
                                group_ok = True

                        if group_ok:
                            # check location
                            location_ok = False
                            new_locations1 = []
                            new_locations2 = []
                            if temp_slot1['locations'] == temp_slot2['locations']:
                                new_locations1 = temp_slot1['locations']
                                new_locations2 = temp_slot1['locations']
                                location_ok = True
                            else:
                                if CsvPreProcessing.check_location_and_generate_possible_locations(dict_lokalen, new_locations1, slot_time, temp_slot1, solution1, day_replace, temp_slot2) and \
                                        CsvPreProcessing.check_location_and_generate_possible_locations(dict_lokalen, new_locations2, slot_time, temp_slot2, solution2, day_replace, temp_slot1):
                                    location_ok = True

                            if location_ok:
                                # check colleagues
                                if sorted(temp_slot1['colleagues']) == sorted(
                                        temp_slot2['colleagues']) and sorted(temp_slot1['groups']) == sorted(temp_slot2['groups']) and temp_slot2['subject'] == temp_slot1['subject'] and temp_slot2['type'] == temp_slot1['type']:
                                    colleagues_ok = True
                                else:
                                    if CsvPreProcessing.check_colleagues_booked(slot_time, solution1, day_replace, temp_slot2, temp_slot1, teacher_to_cross_over) and CsvPreProcessing.check_colleagues_booked(slot_time, solution2, day_replace, temp_slot1, temp_slot2, teacher_to_cross_over):
                                        colleagues_ok = True

                        if colleagues_ok:
                            reset = True
                            # changes_before_reset += 1
                            # switch the teacher slots
                            CsvPreProcessing.plan_slot(new_locations1, slot_time, solution1, day_replace,
                                                       teacher_to_cross_over, temp_slot2)
                            CsvPreProcessing.plan_slot(new_locations2, slot_time, solution2, day_replace,
                                                       teacher_to_cross_over, temp_slot1)
                            # switch colleagues
                            CsvPreProcessing.updating_colleague(new_locations1, slot_time, solution1,
                                                                day_replace, teacher_to_cross_over, temp_slot2)
                            CsvPreProcessing.updating_colleague(new_locations2, slot_time, solution2,
                                                                day_replace, teacher_to_cross_over, temp_slot1)

                            # switch replaced slot on same solution
                            # if temp_slot2['subject'] == 'Desktop OS' or temp_slot2['subject'] == 'Programming Essentials 1':
                            #     print('test')
                            new_slot1 = CsvPreProcessing.get_outgoing_slot_location(days, dict_lokalen, solution1, start_replace, teacher_to_cross_over, temp_slot1, temp_slot2)

                            if new_slot1:
                                # changes_find_new_slot1 += 1
                                new_slot2 = CsvPreProcessing.get_outgoing_slot_location(days, dict_lokalen, solution2, start_replace, teacher_to_cross_over, temp_slot2, temp_slot1)

                                if new_slot2:
                                    CsvPreProcessing.fix_colleagues_from_first_location(day_replace, slot_time,
                                                                                        solution1, between_results2,
                                                                                        temp_slot1)

                                    CsvPreProcessing.fix_colleagues_from_first_location(day_replace, slot_time,
                                                                                        solution2, between_results1,
                                                                                        temp_slot2)
                                    # changes += 1
                                    # switch teacher outgoing slot
                                    temp_locations_switch_slot1 = copy.deepcopy(solution1['solution'][teacher_to_cross_over][days[new_slot1['slot_day_index']]][new_slot1['slot_time']]['locations'])
                                    temp_locations_switch_slot2 = copy.deepcopy(solution2['solution'][teacher_to_cross_over][days[new_slot2['slot_day_index']]][new_slot2['slot_time']]['locations'])
                                    CsvPreProcessing.plan_slot(new_slot1['locations'], new_slot1['slot_time'], solution1,
                                                               days[new_slot1['slot_day_index']],
                                                               teacher_to_cross_over, temp_slot1)
                                    CsvPreProcessing.plan_slot(new_slot2['locations'], new_slot2['slot_time'],
                                                               solution2,
                                                               days[new_slot2['slot_day_index']],
                                                               teacher_to_cross_over, temp_slot2)

                                    # switch colleagues
                                    CsvPreProcessing.updating_colleague(new_slot1['locations'], new_slot1['slot_time'], solution1,
                                                                        days[new_slot1['slot_day_index']], teacher_to_cross_over,
                                                                        temp_slot1)
                                    CsvPreProcessing.updating_colleague(new_slot2['locations'],
                                                                        new_slot2['slot_time'], solution2,
                                                                        days[new_slot2['slot_day_index']],
                                                                        teacher_to_cross_over, temp_slot2)

                                    CsvPreProcessing.fix_colleagues_from_first_location(days[new_slot1['slot_day_index']], new_slot1['slot_time'],
                                                                                        solution1, None,
                                                                                        temp_slot2)

                                    CsvPreProcessing.fix_colleagues_from_first_location(
                                        days[new_slot2['slot_day_index']], new_slot2['slot_time'],
                                        solution2, None,
                                        temp_slot1)

                                    # update tracking dict
                                    CsvPreProcessing.replace_tracking_dict_slot(days, new_locations1, slot_time,
                                                                                solution1, start_replace,
                                                                                teacher_to_cross_over, temp_slot1,
                                                                                temp_slot2)

                                    CsvPreProcessing.replace_tracking_dict_slot(days, new_locations2, slot_time,
                                                                                solution2, start_replace,
                                                                                teacher_to_cross_over, temp_slot2,
                                                                                temp_slot1)

                                    CsvPreProcessing.replace_tracking_dict_slot(days, new_slot1['locations'], new_slot1['slot_time'],
                                                                                solution1, new_slot1['slot_day_index'],
                                                                                teacher_to_cross_over, temp_slot2,
                                                                                temp_slot1, temp_locations_switch_slot1)

                                    CsvPreProcessing.replace_tracking_dict_slot(days, new_slot2['locations'],
                                                                                new_slot2['slot_time'],
                                                                                solution2, new_slot2['slot_day_index'],
                                                                                teacher_to_cross_over, temp_slot1,
                                                                                temp_slot2, temp_locations_switch_slot2)

                                    # for colleague in temp_slot1['colleagues']:
                                    #     CsvPreProcessing.plan_slot(days, new_slot1['locations'], new_slot1['slot_time'],
                                    #                                solution1,
                                    #                                new_slot1['slot_day_index'],
                                    #                                colleague, temp_slot1)
                                    # for colleague in temp_slot2['colleagues']:
                                    #     CsvPreProcessing.plan_slot(days, new_slot2['locations'], new_slot2['slot_time'],
                                    #                                solution2,
                                    #                                new_slot2['slot_day_index'],
                                    #                                colleague, temp_slot2)

                                    reset = False

                            # reset if replaced slot not found
                            if reset:
                                # print('reset')
                                # switch the teacher slots back
                                CsvPreProcessing.plan_slot(between_results1[teacher_to_cross_over][day_replace][slot_time]['locations'], slot_time, solution1, day_replace,
                                                           teacher_to_cross_over, temp_slot1)
                                CsvPreProcessing.plan_slot(between_results2[teacher_to_cross_over][day_replace][slot_time]['locations'], slot_time, solution2, day_replace,
                                                           teacher_to_cross_over, temp_slot2)
                                # switch colleagues slot back
                                CsvPreProcessing.reset_updating_colleague(between_results1, slot_time, solution1, day_replace, temp_slot2)
                                CsvPreProcessing.reset_updating_colleague(between_results2, slot_time, solution2, day_replace, temp_slot1)

                start_replace += 1

        CsvPreProcessing.number_of_mutations(dict_lokalen, mutations, solution1, teachers)
        CsvPreProcessing.number_of_mutations(dict_lokalen, mutations, solution2, teachers)

        # print(f"changes = {changes}")
        # print(f"changes before reset = {changes_before_reset}")
        # print(f"changes reach slot 1 = {changes_find_new_slot1}")

    @staticmethod
    def fix_colleagues_from_first_location(day_replace, slot_time, solution1, between_result, temp_slot1, retrieve_time=None, retrieve_day=None):
        if temp_slot1['colleagues']:
            retrieve_time_par = slot_time
            retrieve_day_par = day_replace
            if retrieve_time:
                retrieve_time_par = retrieve_time
                retrieve_day_par = retrieve_day
            for colleague in temp_slot1['colleagues']:
                if between_result:
                    new_temp_slot2 = copy.deepcopy(between_result[colleague][retrieve_day_par][retrieve_time_par])
                else:
                    new_temp_slot2 = {'subject': '', 'type': '', 'locations': [], 'groups': [], 'location_needs': '',
                                    'colleagues': [], 'amount_of_students': ''}
                CsvPreProcessing.plan_slot(new_temp_slot2['locations'], slot_time, solution1, day_replace,
                                           colleague, new_temp_slot2)

    @staticmethod
    def number_of_mutations(dict_lokalen, mutations, solution, teachers):
        random_mutations = random.randint(1, mutations)
        check_solution1 = copy.deepcopy(solution)

        # number_of_tries = 1
        while random_mutations > 0:
            # check_solution = copy.deepcopy(solution)
            return_value = CsvPreProcessing.mutation(dict_lokalen, solution, teachers)
            random_mutations += return_value

            # if return_value == -1:
            #     print(number_of_tries)
            #     number_of_tries = 1
            # elif number_of_tries == 10000:
            #     random_mutations -= 1
            #     print(f'cap reached - {number_of_tries}')
            #     number_of_tries = 1
            # number_of_tries += 1

    @staticmethod
    def get_day_with_slots(days, solution, teacher_to_mutate):
        while True:
            day = days[random.randint(0, len(days) - 1)]
            if len(list(solution['solution'][teacher_to_mutate][day].keys())) > 0:
                return day

    @staticmethod
    def mutation(dict_lokalen, solution, teachers):
        # mutation
        teacher_to_mutate = teachers[random.randint(0, len(teachers) - 1)]
        days = list(solution['solution'][teacher_to_mutate].keys())
        day1 = CsvPreProcessing.get_day_with_slots(days, solution, teacher_to_mutate)
        day2 = CsvPreProcessing.get_day_with_slots(days, solution, teacher_to_mutate)

        time_slots1 = list(solution['solution'][teacher_to_mutate][day1].keys())
        time_slots2 = list(solution['solution'][teacher_to_mutate][day2].keys())
        time_slot1 = time_slots1[random.randint(0, len(time_slots1) - 1)]
        time_slot2 = time_slots2[random.randint(0, len(time_slots2) - 1)]
        temp_slot1 = copy.deepcopy(solution['solution'][teacher_to_mutate][day1][time_slot1])
        temp_slot2 = copy.deepcopy(solution['solution'][teacher_to_mutate][day2][time_slot2])

        between_result = {}
        for colleague in temp_slot2['colleagues']:
            between_result[colleague] = copy.deepcopy(solution['solution'][colleague])
        between_result[teacher_to_mutate] = copy.deepcopy(solution['solution'][teacher_to_mutate])
        for colleague in temp_slot1['colleagues']:
            if colleague not in between_result:
                between_result[colleague] = copy.deepcopy(solution['solution'][colleague])

        # if (temp_slot1['subject'] or temp_slot2['subject']) and (temp_slot1['subject'] != temp_slot2['subject'] and temp_slot1['type'] != temp_slot2['type']) and temp_slot2['subject'] == 'Desktop OS' and temp_slot1['subject'] == 'Programming Essentials 1':
        if (temp_slot1['subject'] or temp_slot2['subject']) and (temp_slot1['subject'] != temp_slot2['subject'] and temp_slot1['type'] != temp_slot2['type']):
            colleagues_ok = False

            # check group
            group_ok = False
            if sorted(temp_slot1['groups']) == sorted(temp_slot2['groups']):
                group_ok = True
            else:
                if CsvPreProcessing.check_group_available(time_slot2, temp_slot1, solution, day2) and \
                        CsvPreProcessing.check_group_available(time_slot1, temp_slot2, solution, day1):
                    group_ok = True


            if group_ok:
                # check location
                location_ok = False
                new_locations1 = []
                new_locations2 = []
                if temp_slot1['locations'] == temp_slot2['locations']:
                    new_locations1 = temp_slot1['locations']
                    new_locations2 = temp_slot1['locations']
                    location_ok = True
                else:
                    if CsvPreProcessing.check_location_and_generate_possible_locations(dict_lokalen,
                                                                                       new_locations1, time_slot1,
                                                                                       temp_slot1, solution,
                                                                                       day1, temp_slot2) and \
                            CsvPreProcessing.check_location_and_generate_possible_locations(dict_lokalen,
                                                                                            new_locations2, time_slot2,
                                                                                            temp_slot2, solution,
                                                                                            day2, temp_slot1):
                        location_ok = True

                if location_ok:
                    # check colleagues
                    if sorted(temp_slot1['colleagues']) == sorted(
                            temp_slot2['colleagues']) and sorted(temp_slot1['groups']) == sorted(temp_slot2['groups']) and temp_slot2['subject'] == temp_slot1['subject']:
                        colleagues_ok = True
                    else:
                        if CsvPreProcessing.check_colleagues_booked(time_slot1, solution, day1,
                                                                    temp_slot2, temp_slot1, teacher_to_mutate) and CsvPreProcessing.check_colleagues_booked(
                                time_slot2, solution, day2, temp_slot1, temp_slot2, teacher_to_mutate):
                            colleagues_ok = True

            if colleagues_ok:

                # switch the teacher slots
                CsvPreProcessing.plan_slot(new_locations1, time_slot1, solution, day1,
                                           teacher_to_mutate, temp_slot2)
                CsvPreProcessing.plan_slot(new_locations2, time_slot2, solution, day2,
                                           teacher_to_mutate, temp_slot1)
                # switch colleagues
                CsvPreProcessing.updating_colleague(new_locations1, time_slot1, solution,
                                                    day1, teacher_to_mutate, temp_slot2)
                CsvPreProcessing.updating_colleague(new_locations2, time_slot2, solution,
                                                    day2, teacher_to_mutate, temp_slot1)

                CsvPreProcessing.fix_colleagues_from_first_location(day1, time_slot1, solution, between_result,
                                                                    temp_slot1, time_slot2, day2)

                CsvPreProcessing.fix_colleagues_from_first_location(day2, time_slot2, solution, between_result,
                                                                    temp_slot2, time_slot1, day1)

                # update tracking dict
                CsvPreProcessing.replace_tracking_dict_slot(days, new_locations1, time_slot1,
                                                            solution, days.index(day1),
                                                            teacher_to_mutate, temp_slot1,
                                                            temp_slot2, between_result[teacher_to_mutate][day1][time_slot1]['locations'])

                CsvPreProcessing.replace_tracking_dict_slot(days, new_locations2, time_slot2,
                                                            solution, days.index(day2),
                                                            teacher_to_mutate, temp_slot2,
                                                            temp_slot1, between_result[teacher_to_mutate][day2][time_slot2]['locations'])
                return -1

        return 0

    @staticmethod
    def updating_colleague(new_locations1, slot_time, solution1, day, teacher_to_cross_over,
                           temp_slot2):
        if temp_slot2['colleagues']:
            new_temp_slot2 = copy.deepcopy(temp_slot2)
            new_temp_slot2['colleagues'].append(teacher_to_cross_over)
            for colleague in temp_slot2['colleagues']:
                new_temp_slot2['colleagues'].remove(colleague)
                CsvPreProcessing.plan_slot(new_locations1, slot_time, solution1, day,
                                           colleague, new_temp_slot2)
                new_temp_slot2['colleagues'].append(colleague)

    @staticmethod
    def reset_updating_colleague(between_result_solution, slot_time, solution, day, temp_slot2):
        if temp_slot2['colleagues']:
            for colleague in temp_slot2['colleagues']:
                new_temp_slot2 = copy.deepcopy(between_result_solution[colleague][day][slot_time])
                CsvPreProcessing.plan_slot(new_temp_slot2['locations'], slot_time, solution, day,
                                           colleague, new_temp_slot2)

    @staticmethod
    def replace_tracking_dict_slot(days, new_locations, slot_time, solution, day_index, teacher_to_cross_over,
                                   outgoing_slot, incoming_slot, outgoing_slot_locations=None):
        # subject, locations, groups, colleagues
        test_day = days[day_index]
        if outgoing_slot['subject']:
            test_slot_content = solution['usage_tracker'][days[day_index]][slot_time]
            if solution['usage_tracker'][days[day_index]][slot_time]['subject'].find(f"{outgoing_slot['subject']}, ") == -1:
                print(outgoing_slot['subject'])

            else:
                solution['usage_tracker'][days[day_index]][slot_time]['subject'] = solution['usage_tracker'][days[day_index]][slot_time]['subject'].replace(f"{outgoing_slot['subject']}, ", '')
                colleagues = copy.deepcopy(outgoing_slot['colleagues'])
                colleagues.append(teacher_to_cross_over)
                # print(solution['usage_tracker'][days[day_index]][slot_time]['colleagues'])
                # print(colleagues)
                colleagues = list(dict.fromkeys(colleagues))
                for colleague in colleagues:
                    solution['usage_tracker'][days[day_index]][slot_time]['colleagues'].remove(colleague)

                if outgoing_slot_locations:
                    for location in outgoing_slot_locations:
                        solution['usage_tracker'][days[day_index]][slot_time]['locations'].remove(location)
                else:
                    for location in outgoing_slot['locations']:
                        solution['usage_tracker'][days[day_index]][slot_time]['locations'].remove(location)

                for group in outgoing_slot['groups']:
                    solution['usage_tracker'][days[day_index]][slot_time]['groups'].remove(group)
                # solution['usage_tracker'][days[day_index]][slot_time]['groups'] = \
                #     [x for x in
                #      solution['usage_tracker'][days[day_index]][slot_time]['groups'] if
                #      x not in outgoing_slot['groups']]
        if incoming_slot['subject']:
            test_slot_content = solution['usage_tracker'][days[day_index]][slot_time]
            solution['usage_tracker'][days[day_index]][slot_time]['subject'] += f"{incoming_slot['subject']}, "
            colleagues = copy.deepcopy(incoming_slot['colleagues'])
            colleagues.append(teacher_to_cross_over)
            colleagues = list(dict.fromkeys(colleagues))
            for colleague in colleagues:
                solution['usage_tracker'][days[day_index]][slot_time]['colleagues'].append(colleague)

            # update groups
            for group in incoming_slot['groups']:
                solution['usage_tracker'][days[day_index]][slot_time]['groups'].append(group)
            # update locations
            for location in new_locations:
                solution['usage_tracker'][days[day_index]][slot_time]['locations'].append(location)

    @staticmethod
    def get_outgoing_slot_location(days, dict_lokalen, solution, start_replace,
                                   teacher_to_cross_over, incoming_slot, outgoing_slot):
        start_search = days.index(days[start_replace])
        new_slot = None
        while new_slot is None and start_search < len(days):
            if start_replace != start_search:
                new_slot = CsvPreProcessing.check_slot_availability(days,
                                                                    dict_lokalen,
                                                                    new_slot, solution,
                                                                    start_search,
                                                                    teacher_to_cross_over, incoming_slot,
                                                                    outgoing_slot)
            start_search += 1
        if start_replace > 0:
            start_search = days.index(days[start_replace - 1])
        else:
            start_search = 0
        while new_slot is None and start_search >= 0:
            if start_replace != start_search:
                new_slot = CsvPreProcessing.check_slot_availability(days,
                                                                    dict_lokalen,
                                                                    new_slot, solution,
                                                                    start_search,
                                                                    teacher_to_cross_over, incoming_slot,
                                                                    outgoing_slot)
            start_search -= 1
        return new_slot

    @staticmethod
    def check_slot_availability(days, dict_lokalen, new_slot, solution, start_search,
                                teacher_to_cross_over, incoming_slot, outgoing_slot):
        for replace_slot_time, replace_slot_value in solution['solution'][teacher_to_cross_over][days[start_search]].items():
            if replace_slot_value['subject'] == outgoing_slot['subject'] and replace_slot_value['type'] == outgoing_slot[
                'type'] and sorted(replace_slot_value['groups']) == sorted(outgoing_slot['groups']):
                slot_subject = replace_slot_value['subject']

                # check location
                colleagues_ok = False
                location_ok = False
                new_replace_slot_locations = []
                # print(replace_slot_value['locations'])
                # print(incoming_slot['locations'])
                # print(replace_slot_value['locations'] == incoming_slot['locations'])
                if replace_slot_value['locations'] == incoming_slot['locations']:
                    new_replace_slot_locations = replace_slot_value['locations']
                    location_ok = True
                else:
                    if CsvPreProcessing.check_location_and_generate_possible_locations(dict_lokalen,
                                                                                       new_replace_slot_locations,
                                                                                       replace_slot_time,
                                                                                       replace_slot_value,
                                                                                       solution,
                                                                                       days[start_search],
                                                                                       incoming_slot):
                        location_ok = True

                if location_ok:
                    # check colleagues

                    if CsvPreProcessing.check_colleagues_booked(replace_slot_time,
                                                                solution,
                                                                days[start_search],
                                                                incoming_slot, outgoing_slot, teacher_to_cross_over):

                        colleagues_ok = True

                    if colleagues_ok:
                        new_slot_time = replace_slot_time
                        new_slot = {'locations': new_replace_slot_locations, 'slot_time': new_slot_time, 'slot_day_index': start_search}
                        return new_slot
        return new_slot

    @staticmethod
    def plan_slot(new_locations1, slot_time, solution1, day, teacher_to_cross_over, temp_slot2):
        solution1['solution'][teacher_to_cross_over][day][slot_time] = copy.deepcopy(temp_slot2)
        solution1['solution'][teacher_to_cross_over][day][slot_time]['locations'] = new_locations1

    @staticmethod
    def check_colleagues_booked(slot_time, solution, day, incoming_slot, outgoing_slot, teacher_to_cross_over):
        colleagues = copy.deepcopy(incoming_slot['colleagues'])
        colleagues.append(teacher_to_cross_over)
        # check colleague available that time
        for colleague in incoming_slot['colleagues']:
            if day in solution['solution'][colleague].keys():
                if slot_time not in solution['solution'][colleague][day].keys():
                    return False
                else:
                    if colleague in solution['usage_tracker'][day][slot_time]['colleagues']:
                        return False
            else:
                return False

        return True

    @staticmethod
    def check_location_and_generate_possible_locations(dict_lokalen, new_locations, slot_time,
                                                       slot_to_be_replaced, solution_to_receive_new_slot,
                                                       day, incoming_slot):
        if incoming_slot['type'] == 'afstandsonderwijs' or not incoming_slot['subject']:
            return True
        else:
            number_of_groups = len(incoming_slot['locations'])
            temp_locations = copy.deepcopy(
                solution_to_receive_new_slot['usage_tracker'][day][slot_time]['locations'])
            used_locations = [x for x in temp_locations if x not in slot_to_be_replaced['locations']]

            capacity_needed = int(incoming_slot['amount_of_students']) / number_of_groups

            day_of_week_number = datetime.datetime.strptime(day, '%Y-%m-%d').date().weekday()

            special_needs_location = incoming_slot['location_needs'] if incoming_slot['location_needs'] else '/'

            for classroom in dict_lokalen[special_needs_location]:
                if classroom not in used_locations \
                        and int(classroom['Capaciteit']) >= capacity_needed:
                    if day_of_week_number == 4 and classroom['Naam'] == 'B119':
                        fill = number_of_groups
                    else:
                        number_of_groups -= 1
                        used_locations.append(classroom)
                        new_locations.append(classroom)
                        if number_of_groups == 0:
                            return True
            return False

    @staticmethod
    def check_group_available(slot_time, slot_value, solution, day):
        for group in slot_value['groups']:
            core_group = group.split('%')[0]
            if core_group in solution['usage_tracker'][day][slot_time]['groups'] or \
                    group in solution['usage_tracker'][day][slot_time]['groups']:
                return False
        return True

    @staticmethod
    def clean_slot_from_solution_tracking_dict(days, k, solution1, start_replace, temp_slot1):
        if temp_slot1['subject']:
            solution1['usage_tracker'][days[start_replace]][k]['colleagues'] = [x for x in solution1['usage_tracker'][days[start_replace]][k]['colleagues'] if x not in temp_slot1['colleagues']]
            solution1['usage_tracker'][days[start_replace]][k]['locations'] = [x for x in solution1['usage_tracker'][days[start_replace]][k]['locations'] if x not in temp_slot1['locations']]
            solution1['usage_tracker'][days[start_replace]][k]['groups'] = [x for x in solution1['usage_tracker'][days[start_replace]][k]['groups'] if x not in temp_slot1['groups']]
            solution1['usage_tracker'][days[start_replace]][k]['subject'].replace(f"{temp_slot1['subject']}, ", '')

    @staticmethod
    def target_slot_replace(days, dict_lokalen, solution1, start_replace, switched, teacher_to_cross_over, temp_slot2,
                            v):
        switch_with_problems = False
        switched = CsvPreProcessing.launch_search_for_slot_replace(days, dict_lokalen, solution1,
                                                                   start_replace, switch_with_problems,
                                                                   switched, teacher_to_cross_over,
                                                                   temp_slot2, v)
        if switched == "":
            switch_with_problems = True
            CsvPreProcessing.launch_search_for_slot_replace(days, dict_lokalen, solution1,
                                                            start_replace, switch_with_problems,
                                                            switched, teacher_to_cross_over,
                                                            temp_slot2, v)
        return switched

    @staticmethod
    def launch_search_for_slot_replace(days, dict_lokalen, solution1, start_replace, switch_with_problems, switched,
                                       teacher_to_cross_over, temp_slot2, v):
        start_search = days.index(days[start_replace])
        while switched == "" and start_search < len(days):
            switched = CsvPreProcessing.search_slot_and_replace(days, dict_lokalen, solution1,
                                                                start_search, switched,
                                                                teacher_to_cross_over, temp_slot2, v,
                                                                switch_with_problems)

            start_search += 1
        if start_replace > 0:
            start_search = days.index(days[start_replace - 1])
        else:
            start_search = 0
        while switched == "" and start_search >= 0:
            switched = CsvPreProcessing.search_slot_and_replace(days, dict_lokalen, solution1,
                                                                start_search, switched,
                                                                teacher_to_cross_over, temp_slot2, v,
                                                                switch_with_problems)
            start_search -= 1
        return switched

    @staticmethod
    def search_slot_and_replace(days, dict_lokalen, solution1, start_search, switched,
                                teacher_to_cross_over, temp_slot2, v, switch_with_problems):
        for slot_time, value in solution1['solution'][teacher_to_cross_over][days[start_search]].items():
            if value['subject'] == v['subject'] and value['type'] == v['type'] and value['groups'] == \
                    v['groups']:
                # check if groups are booked that time of day else skip to next slot
                if value['groups'] != temp_slot2['groups']:
                    groups_available = True
                    for group in temp_slot2['groups']:
                        core_group = group.split('%')[0]
                        if core_group in solution1['usage_tracker'][days[start_search]][slot_time][
                            'groups'] or group in \
                                solution1['usage_tracker'][days[start_search]][slot_time]['groups']:
                            groups_available = False
                            break
                    if not groups_available:
                        break
                # check if colleagues are booked that time of day else skip to next slot
                # and check if slot exists for colleagues else skip to next slot
                if value['colleagues'] != temp_slot2['colleagues']:
                    colleagues_available = True
                    for colleague in temp_slot2['colleagues']:
                        if days[start_search] not in solution1['solution'][colleague].keys() or (colleague in solution1['usage_tracker'][days[start_search]][slot_time]['colleagues'] and colleague != teacher_to_cross_over):
                            colleagues_available = False
                            break
                    if not colleagues_available:
                        break

                switched = slot_time
                CsvPreProcessing.clean_slot_from_solution_tracking_dict(days, slot_time, solution1, start_search,
                                                                        value)
                switched = CsvPreProcessing.try_fix_locations(days, dict_lokalen, slot_time, solution1,
                                                              start_search, switch_with_problems, switched,
                                                              teacher_to_cross_over, temp_slot2, value)
        return switched

    @staticmethod
    def try_fix_locations(days, dict_lokalen, slot_time, solution1, start_search, switch_with_problems,
                          switched, teacher_to_cross_over, data_slot, value):
        if data_slot['subject']:
            # check if locations if available for incoming slot to this position from solution 1
            if value['locations'] == data_slot['locations'] or data_slot['type'] == 'afstandsonderwijs':
                if data_slot['type'] == 'afstandsonderwijs':
                    solution1['usage_tracker'][days[start_search]][slot_time]['locations'] = [x for x in solution1['usage_tracker'][days[start_search]][slot_time]['locations'] if x not in value['locations']]
                # moved solution1 original position to a suited place
                solution1['solution'][teacher_to_cross_over][days[start_search]][slot_time] = data_slot
                CsvPreProcessing.update_tracking_dict(days, slot_time, solution1,
                                                      start_search, teacher_to_cross_over, data_slot,
                                                      value)

            else:
                number_of_groups = len(data_slot['locations'])
                temp_locations = copy.deepcopy(
                    solution1['usage_tracker'][days[start_search]][slot_time]['locations'])
                temp_locations = [x for x in temp_locations if x not in value['locations']]

                available_classrooms = []
                capacity_needed = int(data_slot['amount_of_students']) / number_of_groups
                day_of_week_number = datetime.datetime.strptime(days[start_search], '%Y-%m-%d').date().weekday()
                speciale_nodes_HOC = data_slot['location_needs'] if data_slot['location_needs'] else '/'
                for classroom in dict_lokalen[speciale_nodes_HOC]:
                    if classroom not in temp_locations \
                            and int(classroom['Capaciteit']) >= capacity_needed:
                        if day_of_week_number == 4 and classroom['Naam'] == 'B119':
                            fill = number_of_groups
                        else:
                            number_of_groups -= 1
                            temp_locations.append(classroom)
                            available_classrooms.append(classroom)
                            if number_of_groups == 0:
                                break

                if number_of_groups == 0 or switch_with_problems:
                    for classroom in available_classrooms:
                        solution1['usage_tracker'][days[start_search]][slot_time]['locations'].append(
                            classroom) if classroom not in \
                                          solution1['usage_tracker'][days[start_search]][slot_time][
                                              'locations'] else \
                            solution1['usage_tracker'][days[start_search]][slot_time]['locations']
                    while number_of_groups > 0:
                        available_classrooms.append('no_location')
                        number_of_groups -= 1
                    solution1['solution'][teacher_to_cross_over][days[start_search]][slot_time] = data_slot
                    solution1['solution'][teacher_to_cross_over][days[start_search]][slot_time][
                        'locations'] = available_classrooms

                    for colleague in data_slot['colleagues']:
                        solution1['solution'][colleague][days[start_search]][slot_time] = data_slot
                        solution1['solution'][colleague][days[start_search]][slot_time][
                            'locations'] = available_classrooms

                    CsvPreProcessing.update_tracking_dict(days, slot_time, solution1,
                                                          start_search, teacher_to_cross_over, data_slot,
                                                          value)
                else:
                    if switch_with_problems:
                        switched = "bad_solution"
                        print("bad solution")
                    else:
                        switched = ""
        else:
            switched = 'ok'
            CsvPreProcessing.update_tracking_dict(days, slot_time, solution1,
                                                  start_search, teacher_to_cross_over, data_slot,
                                                  value)

        return switched

    @staticmethod
    def update_tracking_dict(days, slot_time, solution1, start_search, teacher_to_cross_over, data_slot, value):
        for colleague in data_slot['colleagues']:
            solution1['usage_tracker'][days[start_search]][slot_time]['colleagues'].append(colleague)
        solution1['usage_tracker'][days[start_search]][slot_time][
            'colleagues'].append(teacher_to_cross_over)
        # update subject
        solution1['usage_tracker'][days[start_search]][slot_time][
                    'subject'] += f"{data_slot['subject']}, "
        # update groups
        for group in data_slot['groups']:
            solution1['usage_tracker'][days[start_search]][slot_time]['groups'].append(group)

    # preparing school days slots
    @staticmethod
    def date_range(date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + timedelta(n)

    @staticmethod
    def get_school_days(start_date, end_date, excluded_dates):
        weekdays = [5, 6]
        days_between = []
        for dt in CsvPreProcessing.date_range(start_date, end_date):
            if dt.weekday() not in weekdays:  # to print only the weekdates
                days_between.append(dt.strftime("%Y-%m-%d"))
        return [x for x in days_between if x not in excluded_dates]

    @staticmethod
    def add_slots_to_school_days(school_days, morning_slots, afternoon_slots, day_of_week_half_day):
        days_with_slots = {}
        for day in school_days:
            if datetime.datetime.strptime(day, '%Y-%m-%d').date().weekday() == day_of_week_half_day:
                days_with_slots[day] = copy.deepcopy(afternoon_slots)
            else:
                days_with_slots[day] = {**copy.deepcopy(morning_slots), **copy.deepcopy(afternoon_slots)}
        return days_with_slots

    @staticmethod
    def get_availability_teacher(dict_docenten, teacher_name, excluded_fixed_weekdays, excluded_half_weekdays,
                                 index_day):
        if dict_docenten[teacher_name][index_day] == "niet":
            excluded_fixed_weekdays.append(index_day)
        elif dict_docenten[teacher_name][index_day] == "voormiddag":
            excluded_half_weekdays[str(index_day)] = 'afternoon'
        elif dict_docenten[teacher_name][index_day] == "namiddag":
            excluded_half_weekdays[str(index_day)] = 'morning'

    @staticmethod
    def add_days_to_teachers(dict_docenten, days_with_slots, morning_slots, afternoon_slots):
        teachers_with_days = {}
        for teacher_name in dict_docenten:
            teachers_with_days[teacher_name] = copy.deepcopy(days_with_slots)
            excluded_days = dict_docenten[teacher_name][5]
            excluded_fixed_weekdays = []
            excluded_half_weekdays = {}
            CsvPreProcessing.get_availability_teacher(dict_docenten, teacher_name, excluded_fixed_weekdays,
                                                      excluded_half_weekdays, 0)
            CsvPreProcessing.get_availability_teacher(dict_docenten, teacher_name, excluded_fixed_weekdays,
                                                      excluded_half_weekdays, 1)
            CsvPreProcessing.get_availability_teacher(dict_docenten, teacher_name, excluded_fixed_weekdays,
                                                      excluded_half_weekdays, 2)
            CsvPreProcessing.get_availability_teacher(dict_docenten, teacher_name, excluded_fixed_weekdays,
                                                      excluded_half_weekdays, 3)
            CsvPreProcessing.get_availability_teacher(dict_docenten, teacher_name, excluded_fixed_weekdays,
                                                      excluded_half_weekdays, 4)

            for day in teachers_with_days[teacher_name]:
                day_of_week_number = datetime.datetime.strptime(day, '%Y-%m-%d').date().weekday()
                if day_of_week_number in excluded_fixed_weekdays:
                    excluded_days.append(day)
                elif str(day_of_week_number) in excluded_half_weekdays.keys():
                    slots_to_remove = morning_slots if excluded_half_weekdays[
                                                           str(day_of_week_number)] == "morning" else afternoon_slots
                    for slot_time in slots_to_remove.keys():
                        teachers_with_days[teacher_name][day].pop(slot_time, None)

            # remove all excluded days
            for day in excluded_days:
                teachers_with_days[teacher_name].pop(day, None)
        return teachers_with_days

    # get different weeknumbers for the dates and add available dates to it
    @staticmethod
    def get_weeknumbers_with_days(school_days):
        dict_weeknumbers_days = {}
        for day in school_days:
            week_number = datetime.datetime.strptime(day, '%Y-%m-%d').date().isocalendar()[1]
            if str(week_number) not in dict_weeknumbers_days.keys():
                dict_weeknumbers_days[str(week_number)] = []
            dict_weeknumbers_days[str(week_number)].append(day)
        return dict_weeknumbers_days

    @staticmethod
    def common_elements(list1, list2):
        return [element for element in list1 if element in list2]

    # initial planning algorithm
    @staticmethod
    def class_planner(p_week_numbers_days, ratio, docenten_HOC, teachers_with_days, aantal_groepen_HOC,
                      speciale_nodes_HOC, dict_lokalen, dict_tracking_days_slots_teachers_groups, aantal_uur_HOC,
                      lesblok, subject_naam, opleiding, aantal_studenten, type_of_class):
        # if subject_naam == 'Desktop OS':
        #     print("stop")
        remaining_teaching_hours = int(aantal_uur_HOC)
        week_numbers_days = copy.deepcopy(p_week_numbers_days)
        if lesblok[0]:
            amount_of_weeks = math.floor(len(week_numbers_days) / int(lesblok[1]))
            if lesblok[0] != lesblok[1] and lesblok[0] != '1':
                weeks_to_remove = (amount_of_weeks * (int(lesblok[0]) - 1))
                while weeks_to_remove > 0:
                    week_numbers_days.pop(week_numbers_days.keys()[0], None)
            else:
                if lesblok[0] == lesblok[1]:
                    amount_of_weeks = len(week_numbers_days) - (amount_of_weeks * (int(lesblok[1]) - 1))
                week_numbers_days = dict(islice(week_numbers_days.items(), amount_of_weeks))

        for week_number in week_numbers_days.keys():
            week_hours = int(ratio)
            for day in week_numbers_days[week_number]:
                available_day_slots_teachers = []
                both_working = True
                for teacher in docenten_HOC:
                    available_slots_teacher = []
                    if teachers_with_days[teacher].keys() and day in teachers_with_days[teacher].keys():
                        for slot in teachers_with_days[teacher][day]:
                            if teachers_with_days[teacher][day][slot]['subject'] == "":
                                available_slots_teacher.append(slot)
                        if not available_slots_teacher:
                            both_working = False
                        if available_day_slots_teachers:
                            available_day_slots_teachers = CsvPreProcessing.common_elements(
                                available_day_slots_teachers, available_slots_teacher)
                        else:
                            available_day_slots_teachers = available_slots_teacher

                    else:
                        both_working = False

                if both_working:
                    day_of_week_number = datetime.datetime.strptime(day, '%Y-%m-%d').date().weekday()
                    for slot in available_day_slots_teachers:
                        # before assignment check if subject and class is already in use
                        number_of_groups = int(aantal_groepen_HOC)
                        if type_of_class != 'afstandsonderwijs':
                            available_classrooms = []
                            capacity_needed = int(aantal_studenten) / number_of_groups
                            speciale_nodes_HOC = speciale_nodes_HOC if speciale_nodes_HOC else '/'
                            for classroom in dict_lokalen[speciale_nodes_HOC]:
                                if classroom not in dict_tracking_days_slots_teachers_groups[day][slot]['locations'] \
                                        and int(classroom['Capaciteit']) >= capacity_needed:
                                    if day_of_week_number == 4 and classroom['Naam'] == 'B119':
                                        fill = number_of_groups
                                    else:
                                        number_of_groups -= 1
                                        available_classrooms.append(classroom)
                                        if number_of_groups == 0:
                                            break
                        booked = False
                        for group in opleiding:
                            core_group = group.split('%')[0]
                            if core_group in dict_tracking_days_slots_teachers_groups[day][slot]['groups'] or \
                                    group in dict_tracking_days_slots_teachers_groups[day][slot]['groups']:
                                booked = True
                                break
                        if not booked and number_of_groups == 0:
                            dict_not_updated = True
                            for teacher in docenten_HOC:
                                teachers_with_days[teacher][day][slot]['subject'] = subject_naam
                                teachers_with_days[teacher][day][slot]['amount_of_students'] = aantal_studenten
                                teachers_with_days[teacher][day][slot]['location_needs'] = speciale_nodes_HOC
                                colleagues = copy.deepcopy(docenten_HOC)
                                colleagues.remove(teacher)
                                teachers_with_days[teacher][day][slot]['colleagues'] = colleagues
                                teachers_with_days[teacher][day][slot]['type'] = type_of_class
                                teachers_with_days[teacher][day][slot]['groups'] = opleiding
                                if dict_not_updated:
                                    dict_tracking_days_slots_teachers_groups[day][slot]['subject'] += f'{subject_naam}, '
                                    dict_tracking_days_slots_teachers_groups[day][slot]['groups'] =\
                                        dict_tracking_days_slots_teachers_groups[day][slot]['groups'] + opleiding
                                    dict_not_updated = False
                                dict_tracking_days_slots_teachers_groups[day][slot]['colleagues'].append(teacher)
                                for group in opleiding:
                                    split_group = group.split('%')
                                    if len(split_group) > 1:
                                        dict_tracking_days_slots_teachers_groups[day][slot]['groups'] = \
                                            dict_tracking_days_slots_teachers_groups[day][slot]['groups'] + [split_group[0]]
                                if type_of_class == 'afstandsonderwijs':
                                    teachers_with_days[teacher][day][slot]['locations'] = ['afstandsonderwijs']
                                else:
                                    teachers_with_days[teacher][day][slot]['locations'] = available_classrooms
                                    dict_tracking_days_slots_teachers_groups[day][slot][
                                        'locations'] += available_classrooms
                            remaining_teaching_hours -= 1
                            if remaining_teaching_hours == 0:
                                return 0
                            week_hours -= 1
                            if week_hours == 0:
                                break
                if week_hours == 0:
                    break
        if remaining_teaching_hours == int(aantal_uur_HOC):
            return remaining_teaching_hours
        else:
            return CsvPreProcessing.class_planner(p_week_numbers_days, ratio, docenten_HOC, teachers_with_days,
                                                  aantal_groepen_HOC,
                                                  speciale_nodes_HOC, dict_lokalen,
                                                  dict_tracking_days_slots_teachers_groups,
                                                  str(remaining_teaching_hours), lesblok, subject_naam, opleiding,
                                                  aantal_studenten, type_of_class)

    @staticmethod
    def building_solution(days_with_slots, school_days, dict_subjects, teachers_with_days, dict_lokalen,
                          dict_tracking_days_slots_teachers_groups):
        not_scheduled_subjects = []
        week_numbers_days = CsvPreProcessing.get_weeknumbers_with_days(school_days)

        intro_subjects = []
        for subject in dict_subjects:
            aantal_uur_HOC = subject['aantal_uur_HOC']
            aantal_uur_WEC = subject['aantal_uur_WEC']
            aantal_uur_afstandsonderwijs = subject['aantal_uur_afstandsonderwijs']
            total_contact_hours = int(aantal_uur_HOC if aantal_uur_HOC else "0") + \
                                  int(aantal_uur_WEC if aantal_uur_WEC else "0") + \
                                  int(aantal_uur_afstandsonderwijs if aantal_uur_afstandsonderwijs else "0")
            if total_contact_hours < 10:
                intro_subjects.append(subject)

        dict_subjects = [elem for elem in dict_subjects if elem not in intro_subjects]

        np.random.shuffle(intro_subjects)
        np.random.shuffle(dict_subjects)
        CsvPreProcessing.generate_solution(intro_subjects, not_scheduled_subjects, week_numbers_days,
                                           teachers_with_days,
                                           dict_lokalen, dict_tracking_days_slots_teachers_groups)
        CsvPreProcessing.generate_solution(dict_subjects, not_scheduled_subjects, week_numbers_days, teachers_with_days,
                                           dict_lokalen, dict_tracking_days_slots_teachers_groups)

        return not_scheduled_subjects

    @staticmethod
    def generate_solution(dict_subjects, not_scheduled_subjects, week_numbers_days, teachers_with_days, dict_lokalen,
                          dict_tracking_days_slots_teachers_groups):
        for subject in dict_subjects:
            # extracting values for overview. Might be deleted in later version
            subject_naam = subject['Naam']
            docenten_HOC = subject['Docenten_HOC']
            docenten_WEC = subject['Docenten_WEC']
            docenten_afstandsonderwijs = subject['Docenten_Afstandsonderwijs']
            opleiding = subject['opleiding']
            aantal_groepen_HOC = subject['aantal_groepen_HOC']
            aantal_groepen_WEC = subject['aantal_groepen_WEC']
            aantal_uur_HOC = subject['aantal_uur_HOC']
            aantal_uur_WEC = subject['aantal_uur_WEC']
            aantal_uur_afstandsonderwijs = subject['aantal_uur_afstandsonderwijs']
            ratio_uren_HOC_vs_WEC_vs_afstand = subject['ratio_uren_HOC_vs_WEC_vs_afstand']
            aantal_studenten = subject['aantal_studenten']
            speciale_nodes_HOC = subject['speciale_nodes_HOC']
            speciale_nodes_WEC = subject['speciale_nodes_WEC']
            lesblok = subject['lesblok']
            # building algorithm
            if docenten_HOC[0]:
                remaining_hours = CsvPreProcessing.class_planner(week_numbers_days, ratio_uren_HOC_vs_WEC_vs_afstand[0],
                                                                 docenten_HOC, teachers_with_days, aantal_groepen_HOC,
                                                                 speciale_nodes_HOC, dict_lokalen,
                                                                 dict_tracking_days_slots_teachers_groups,
                                                                 aantal_uur_HOC,
                                                                 lesblok, subject_naam, opleiding, aantal_studenten,
                                                                 'HOC')
                if remaining_hours != 0:
                    not_scheduled_subjects.append([subject_naam, 'HOC', remaining_hours])
            if docenten_WEC[0]:
                remaining_hours = CsvPreProcessing.class_planner(week_numbers_days, ratio_uren_HOC_vs_WEC_vs_afstand[1],
                                                                 docenten_WEC,
                                                                 teachers_with_days, aantal_groepen_WEC,
                                                                 speciale_nodes_WEC,
                                                                 dict_lokalen, dict_tracking_days_slots_teachers_groups,
                                                                 aantal_uur_WEC,
                                                                 lesblok, subject_naam, opleiding, aantal_studenten,
                                                                 'WEC')
                if remaining_hours != 0:
                    not_scheduled_subjects.append([subject_naam, 'WEC', remaining_hours])
            if docenten_afstandsonderwijs[0]:
                remaining_hours = CsvPreProcessing.class_planner(week_numbers_days, ratio_uren_HOC_vs_WEC_vs_afstand[2],
                                                                 docenten_afstandsonderwijs, teachers_with_days, '0',
                                                                 '', dict_lokalen,
                                                                 dict_tracking_days_slots_teachers_groups,
                                                                 aantal_uur_afstandsonderwijs,
                                                                 lesblok, subject_naam, opleiding, aantal_studenten,
                                                                 'afstandsonderwijs')
                if remaining_hours != 0:
                    not_scheduled_subjects.append([subject_naam, 'afstandsonderwijs', remaining_hours])

    @staticmethod
    def fitness_function(teachers_with_days, days_with_slots, dict_overview_subjects):
        dict_groups = {}
        solution_points = 0
        solution_between = copy.deepcopy(teachers_with_days)
        # evaluation teachers
        for teacher in teachers_with_days:
            for day in teachers_with_days[teacher].keys():
                full_day = True
                previous_slot = False
                for slot in teachers_with_days[teacher][day].keys():
                    if teachers_with_days[teacher][day][slot]['subject']:
                        if previous_slot:
                            solution_points += CsvPreProcessing.teacher_has_chaining_subject
                            if 'afstandsonderwijs' in teachers_with_days[teacher][day][slot]['locations']:
                                full_day = False
                        previous_slot = True
                        # add group to new dict
                        for group in teachers_with_days[teacher][day][slot]['groups']:
                            if group not in dict_groups.keys():
                                dict_groups[group] = copy.deepcopy(days_with_slots)
                            dict_groups[group][day][slot] = copy.deepcopy(teachers_with_days[teacher][day][slot])
                    else:
                        previous_slot = False
                        full_day = False
                if full_day:
                    solution_points += CsvPreProcessing.teacher_has_full_day

        # fix possible full days for specialisation
        dict_specialisation_groups = {}
        for group in dict_groups:
            groups = group.split('%')
            if len(groups) > 1:
                if groups[0] not in dict_specialisation_groups.keys():
                    dict_specialisation_groups[groups[0]] = {'groups': []}
                dict_specialisation_groups[groups[0]]['groups'].append(group)
                for day in dict_groups[group]:
                    for slot in dict_groups[group][day].keys():
                        if dict_groups[group][day][slot]['subject']:
                            subject = dict_groups[group][day][slot]['subject']
                            if dict_groups[groups[0]][day][slot]['subject'] and dict_groups[groups[0]][day][slot]['subject'] not in dict_groups[group][day][slot]['subject'].split('%'):
                                dict_groups[groups[0]][day][slot]['subject'] += f'%{subject}'
                            else:
                                dict_groups[groups[0]][day][slot]['subject'] = subject
                            dict_groups[groups[0]][day][slot]['locations'] = \
                                dict_groups[groups[0]][day][slot]['locations'] + \
                                dict_groups[group][day][slot]['locations']
                            # adding specialisation subject key to groups and type
                            temp_subject = dict_groups[group][day][slot]['subject']
                            temp_groups = '%'.join(dict_groups[group][day][slot]['groups'])

                            temp_string = f"{temp_subject}%{temp_groups}|{dict_groups[group][day][slot]['type']}"
                            dict_groups[groups[0]][day][slot]['groups'].append(temp_string)
        # evaluation students
        for group in dict_groups:
            if len(group.split('%')) == 1:
                for day in dict_groups[group].keys():
                    full_day = True
                    previous_slot = False
                    previous_locations = []
                    previous_subject = ''
                    for slot in dict_groups[group][day].keys():
                        if dict_groups[group][day][slot]['subject']:
                            # generate subject weekly sequence
                            split_groups = dict_groups[group][day][slot]['groups'][0].split('|')
                            if len(split_groups) > 1:
                                for record in dict_groups[group][day][slot]['groups']:
                                    split_record = record.split('|')
                                    CsvPreProcessing.create_subject_list(split_record[0], day,
                                                                         dict_overview_subjects, split_record[1])
                            else:
                                piece1 = f"{dict_groups[group][day][slot]['subject']}%"
                                piece2 = f"{'%'.join(dict_groups[group][day][slot]['groups'])}"

                                subjects = dict_groups[group][day][slot]['subject'].split('%')
                                if len(subjects) > 1:
                                    for sub_subject in subjects:
                                        for check_group in dict_groups:
                                            if group in check_group and check_group != group:
                                                if day in dict_groups[check_group].keys():
                                                    if slot in dict_groups[check_group][day].keys():
                                                        if dict_groups[check_group][day][slot]['subject'] == sub_subject:
                                                            sub_subject_key = f"{sub_subject}%" \
                                                                          f"{'%'.join(dict_groups[check_group][day][slot]['groups'])}"
                                                            CsvPreProcessing.create_subject_list(sub_subject_key, day,
                                                                                                 dict_overview_subjects,
                                                                                                 dict_groups[check_group][day][slot]['type'])
                                else:
                                    sub_subject = dict_groups[group][day][slot]['subject']
                                    if len(dict_groups[group][day][slot]['groups'][0].split('%')) > 1:
                                        for check_group in dict_groups:
                                            if group in check_group and check_group != group:
                                                if day in dict_groups[check_group].keys():
                                                    if slot in dict_groups[check_group][day].keys():
                                                        if dict_groups[check_group][day][slot]['subject'] == sub_subject:
                                                            subject_key = f"{sub_subject}%" \
                                                                          f"{'%'.join(dict_groups[check_group][day][slot]['groups'])}"
                                                            CsvPreProcessing.create_subject_list(subject_key, day,
                                                                                                 dict_overview_subjects,
                                                                                                 dict_groups[check_group][day][slot]['type'])
                                    else:
                                        subject_key = f"{sub_subject}%" \
                                                      f"{'%'.join(dict_groups[group][day][slot]['groups'])}"
                                        CsvPreProcessing.create_subject_list(subject_key, day,
                                                                             dict_overview_subjects,
                                                                             dict_groups[group][day][slot]['type'])

                            # evaluation students
                            subjects = dict_groups[group][day][slot]['subject'].split('%')
                            if group in dict_specialisation_groups.keys() and \
                                    len(subjects) == len(dict_specialisation_groups[group]['groups']):
                                solution_points += CsvPreProcessing.specialisation_same_hour
                            if previous_slot:
                                solution_points += CsvPreProcessing.student_has_chaining_subject
                                if 'afstandsonderwijs' in dict_groups[group][day][slot]['locations']:
                                    full_day = False
                                if previous_subject == dict_groups[group][day][slot]['subject']:
                                    solution_points += CsvPreProcessing.student_has_same_subject
                                    if previous_locations == dict_groups[group][day][slot]['locations']:
                                        solution_points += CsvPreProcessing.student_stays_in_same_room
                                if previous_locations == dict_groups[group][day][slot]['locations'] \
                                        and previous_subject == \
                                        dict_groups[group][day][slot]['subject']:
                                    solution_points += CsvPreProcessing.student_stays_in_same_room_for_same_subject
                            previous_slot = True
                            previous_subject = dict_groups[group][day][slot]['subject']
                            previous_locations = dict_groups[group][day][slot]['locations']
                        else:
                            previous_slot = False
                            previous_subject = ''
                            previous_locations = []
                            full_day = False
                    if full_day:
                        solution_points += CsvPreProcessing.student_has_full_day

        # evaluating subjects
        for sub_subject in dict_overview_subjects.keys():
            ratio = dict_overview_subjects[sub_subject]['ratio']
            for week in dict_overview_subjects[sub_subject]['weeks'].keys():
                week_overview = dict_overview_subjects[sub_subject]['weeks'][week]
                if week_overview['first_hoc']:
                    solution_points += CsvPreProcessing.first_hoc_vs_other
                if str(week_overview['HOC']) == ratio[0] and \
                        str(week_overview['WEC']) == ratio[1] and \
                        str(week_overview['afstandsonderwijs']) == ratio[2]:
                    solution_points += CsvPreProcessing.week_ratio_respected

        return solution_points

    @staticmethod
    def create_subject_list(subject, day, dict_overview_subjects, counter_to_update):
        week_number = str(datetime.datetime.strptime(day, '%Y-%m-%d').date().isocalendar()[1])
        dict_overview_subjects[subject]['weeks'][week_number][counter_to_update] += 1
        ratio = dict_overview_subjects[subject]['ratio']
        if counter_to_update != "HOC":
            if int(dict_overview_subjects[subject]['weeks'][week_number]['HOC']) >= int(ratio[0]):
                dict_overview_subjects[subject]['weeks'][week_number]['first_hoc'] = False
        dict_overview_subjects[subject]['weeks'][week_number]['week_scheduled'] = True

    @staticmethod
    def retrieve_top_solutions_for_next_gen(solutions, solutions_drop_ratio):
        solutions_df = pd.DataFrame(solutions)
        solutions_df = solutions_df.sort_values(by="score", ascending=False)
        solutions_df = solutions_df.drop_duplicates(subset=['score'], keep='first')

        row_count = solutions_df.shape[0]
        rows_to_delete = round(row_count * solutions_drop_ratio)

        if not rows_to_delete % 2 == 0:
            rows_to_delete -= 1

        solutions_df = solutions_df[:-rows_to_delete]

        return solutions_df.to_dict('records')


def main():
    print("Test function")
    t0 = time.time()
    csv_preprocessing = CsvPreProcessing()
    t1 = time.time()

    total = t1 - t0
    print(total)


if __name__ == '__main__':
    main()

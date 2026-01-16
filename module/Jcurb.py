# import os
# from PIL import Image
# import pandas as pd
# import streamlit as st
# import const.constpara as co
# import extra_streamlit_components as stx
# from st_aggrid import AgGrid, JsCode, GridOptionsBuilder, GridUpdateMode
# import datetime
# import json
# import module.dialog as dia
# import module.grid_option as gop
# import module.utils as utl
# from module.PsqlModule import psql_class
# import time
# import plotly.express as px
# import plotly.graph_objects as go
# import time
# # import win32com.client
# # from win32com.client import gencache
# # import pythoncom
# from itertools import cycle
# import numpy as np
# # import win32gui
# # import win32con
# import signal
# import psutil
#
# # CSSファイルの内容を読み込む
# with open(co.css, encoding='utf-8') as f:
#     css = f.read()
#
# with open(co.css_ag, encoding='utf-8') as f:
#     css_ag = json.load(f)
#
# sql = psql_class()
# # CSSをStreamlitに適用
# st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
#
# cell_highlight = JsCode("""
# function(params) {
# 	if(params.node.rowIndex() === 0){
# 		return{
# 			"backgroundColor":"#000000"
# 		}
# 	};
# 	return null;
# }
# """)
#
# # 列のスタイルを決定する関数
# def get_column_style(df, column_name):
#     # 各列の値を取得
#     column_values = df[column_name].dropna().tolist()
#     # 列内の値が異なる場合
#     if len(set(column_values)) > 1:
#         return {'backgroundColor': 'lightcoral'}
#     return {}
#
# def back_to_SPDM_LIST():
#
#
#     st.switch_page("./pages/SPDM_LIST.py")
#
# def close_excel_popups(): # kill all excel popup, prevent surrogate model mulfunction
#     def callback(hwnd, _):
#         title = win32gui.GetWindowText(hwnd)
#         class_name = win32gui.GetClassName(hwnd)
#         if "Excel" in title or class_name == 'XLMAIN':
#             try:
#                 win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
#             except Exception as e:
#                 print('failed to close window:', e)
#     win32gui.EnumWindows(callback, None)
#
# def kill_excel():
#     for proc in psutil.process_iter(['name']):
#         if proc.info['name'] and 'EXCEL.EXE' in proc.info['name']:
#
#             proc.kill()
#
# def calc_delta_cost(df_cost, parameter, variable_change):
#     #item_nameは最後のだけでなく全部表示させる
#     if variable_change == 0:
#         return 0,''
#     try:
#         delta_cost = df_cost[df_cost['parameter_change_accumulate']<=variable_change]['cost_change_accumulate'].tolist()[0]
#         item_name = df_cost[df_cost['parameter_change_accumulate']<=variable_change]['part_name_accumulate'].tolist()[0]
#     except IndexError:
#         delta_cost = df_cost['cost_change_accumulate'].tolist()[-1]
#         item_name = df_cost['part_name_accumulate'].tolist()[-1]
#
#     return delta_cost, item_name
# class Plotter():
#
#     def __init__(self):
#         self.scatter_count = 0
#         self.parallel_coordinate_count = 0
#         self.Jcurb_count = 0
#
#     def color_for_studies(self, list_study_ids=[]):
#         list_study_ids = [True, False, 'Satisfied', 'Base', 'surrogate_estimated', 'selected_from_Jcurb'] + list_study_ids
#         plotly_colors = [
#         'green', 'cyan', 'red', 'blue','orange', 'blue', 'purple', 'magenta', 'yellow',
#         'lime', 'pink', 'teal', 'brown', 'black', 'gray', 'indigo', 'violet',
#         'gold', 'silver', 'navy', 'maroon', 'olive', 'coral', 'turquoise', 'darkgreen'
#     ]
#         color_cycle = cycle(plotly_colors)
#         return {id_: next(color_cycle) for id_ in list_study_ids}
#
#
#     def plot_scatter(self, df_sampling, X_axis, Y_axis, X_range, Y_range, list_study_ids=[], df_line_plot=None):
#         #各スタディもプロットさせたいとなったとき、それぞれのスタディごとにsize,color,symbolを順番に設定できるようにしなければいけない？？？？
#         self.scatter_count += 1
#         color_map = self.color_for_studies(list_study_ids=list_study_ids)
#         df_sampling =df_sampling[df_sampling['flag_pareto'].isin(list_study_ids + [True, False, 'Satisfied','Base','surrogate_estimated','selected_from_Jcurb'])]
#         df_sampling['size'] = df_sampling['flag_pareto'].map({True:10,False:5, 'Satisfied':15, 'Base':15, 'surrogate_estimated':20}).fillna(25)
#         df_sampling['color'] = df_sampling['flag_pareto'].map(color_map)
#         df_sampling['symbol'] = df_sampling['flag_pareto'].map({True:'diamond', False:'circle-open', 'Satisfied':'x', 'Base':'circle', 'surrogate_estimated':'cross', 'selected_from_Jcurb':'circle'}).fillna('star')
#         # df_sampling['all_names'] = df_sampling['all_names'].replace('\|','<br>',regex=True) #ホバー内で改行するため置き換える
#         df_sampling = df_sampling.fillna(0)
#         #px.scatterの基本的な使い方では、最初にXのデータ、Yのデータなど指定するのが普通であるが、ここではそうしていない
#         #理由：px.scatterからプロットの色、形が指定できないがupdate_tracesからはできる→update_tracesでアップデートした情報とpx.scatterで入れた情報で行がずれる？？→すべてupdate_traces経由で入れることでむりくり解決
#         # fig = px.scatter(df_sampling.copy(), x=X_axis, y=Y_axis, range_x=X_range, range_y=Y_range)
#         fig = go.Figure()
#         for category in df_sampling['flag_pareto'].unique():
#
#             df_group = df_sampling[df_sampling['flag_pareto'] == category]
#             fig.add_trace(go.Scatter(
#                     x=df_group[X_axis],
#                     y=df_group[Y_axis],
#                     mode='markers',
#                     marker=dict(
#                         color=df_group['color'],
#                         size=df_group['size'],
#                         symbol=df_group['symbol']
#                     ),
#                     name=str(category),  # This will show in the legend
#                     showlegend=True
#                 ))
#
#
#         # fig.update_traces(marker=dict(color=df_sampling['color'], size=df_sampling['size'], symbol=df_sampling['symbol']),
#         #                 #   selector=dict(mode='markers+text'), because of you nothing were working
#         #                   x=df_sampling[X_axis],
#         #                   y=df_sampling[Y_axis],
#         #                   customdata=df_sampling[['all_names','<ID>']].to_numpy(),
#         #                 #   hovertemplate='<b>Items</b><br><br> %{customdata[0]}<extra>%{customdata[1]}</extra>',
#         #                 #   hoverlabel=dict(font=dict(size=30, color='blue')), ホバーを無効か6/17
#         #                   name=str('')
#         #                   showlegend=True
#         #                   )
#         fig.update_layout(width=800, height=800,
#                         autosize=False,
#                         xaxis_title=X_axis,
#                         yaxis_title=Y_axis
#                         #   legend=dict(
#
#                         #       title=dict(text='flag_pareto'),
#                         #       tracegroupgap=0
#                         #   )
#                           )
#         ##制約線表示機能追加
#         if df_line_plot is not None :
#             if len(df_line_plot[df_line_plot['parameter_name']==X_axis])>0:
#                 X_line_value = df_line_plot[df_line_plot['parameter_name']==X_axis]['referenced_value'].tolist()[0]
#             else :
#                 X_line_value = None
#             if len(df_line_plot[df_line_plot['parameter_name']==Y_axis])>0:
#                 Y_line_value = df_line_plot[df_line_plot['parameter_name']==Y_axis]['referenced_value'].tolist()[0]
#             else:
#                 Y_line_value = None
#
#             if Y_line_value is not None:
#                 fig.add_shape(
#                     type = "line",
#                     x0 = min(X_range),
#                     x1 = max(X_range),
#                     y0 = Y_line_value,
#                     y1 = Y_line_value,
#                     line = dict(color='red', width=2, dash='dash'),
#                 )
#             if X_line_value is not None:
#                 fig.add_shape(
#                     type = "line",
#                     y0 = min(Y_range),
#                     y1 = max(Y_range),
#                     x0 = X_line_value,
#                     x1 = X_line_value,
#                     line = dict(color='red', width=2, dash='dash'),
#                 )
#         print(fig)
#         return st.plotly_chart(fig, on_select='rerun', key='scatter_' + str(self.scatter_count), use_container_width=False)
#
#     # #07/30 #Kyaw #Add Z_axis
#     # def plot_scatter(self, df_sampling, X_axis, Y_axis, X_range, Y_range, Z_axis=None):
#
#     #     self.scatter_count += 1
#
#     #     df_sampling['size'] = df_sampling['flag_pareto'].map({True:10, False:5, 'Satisfied':15, 'Base':15})
#     #     df_sampling['color'] = df_sampling['flag_pareto'].map({True:'green', False:'cyan', 'Satisfied':'red', 'Base':'blue'})
#     #     df_sampling['symbol'] = df_sampling['flag_pareto'].map({True:'diamond', False:'circle-open', 'Satisfied':'x', 'Base':'circle'})
#     #     df_sampling['all_names'] = df_sampling['all_names'].replace('\|','<br>', regex=True)
#
#     #     # Create scatter plot
#     #     fig = px.scatter(df_sampling.copy(), x=X_axis, y=Y_axis, range_x=X_range, range_y=Y_range)
#
#     #     fig.update_traces(
#     #         marker=dict(
#     #             color=df_sampling['color'],
#     #             size=df_sampling['size'],
#     #             symbol=df_sampling['symbol']
#     #         ),
#     #         x=df_sampling[X_axis],
#     #         y=df_sampling[Y_axis],
#     #         customdata=df_sampling[['all_names','<ID>']].to_numpy(),
#     #         showlegend=True
#     #     )
#
#     #     # === Add Contour Plot if Z_axis is specified ===
#     #     if Z_axis:
#     #         # Grid resolution
#     #         # num_grid = 100
#
#     #         num_points = len(df_sampling)
#     #         num_grid = min(200, max(50, int(num_points ** 0.5)))
#     #         # st.write('num grid: ',num_grid)
#
#     #         # Create grid coordinates
#     #         x = df_sampling[X_axis]
#     #         y = df_sampling[Y_axis]
#     #         z = df_sampling[Z_axis]
#
#     #         xi = np.linspace(X_range[0], X_range[1], num_grid)
#     #         yi = np.linspace(Y_range[0], Y_range[1], num_grid)
#     #         xi, yi = np.meshgrid(xi, yi)
#
#     #         # st.write('xi: ', xi)
#     #         # st.write('yi: ', yi)
#
#     #         # Interpolate Z values on the grid
#     #         zi = griddata((x, y), z, (xi, yi), method='cubic')
#     #         # st.write('zi: ', zi)
#     #         # Add contour trace
#     #         fig.add_trace(go.Contour(
#     #             z=zi,
#     #             x=xi[0],
#     #             y=yi[:, 0],
#     #             colorscale='ylorbr',
#     #             contours=dict(
#     #                 coloring='fill',
#     #                 showlines=True
#     #             ),
#     #             showscale=True,
#     #             opacity=0.5,
#     #             colorbar=dict(
#     #                 title=f'{Z_axis}',
#     #                 # side='right'
#     #             ),
#     #             # hoverinfo='skip'
#     #             hovertemplate=f'{X_axis}: %{{x}}<br>{Y_axis}: %{{y}}<br>{Z_axis}: %{{z}}<extra></extra>'
#     #         ))
#
#     #     fig.update_layout(
#     #         width=2000,
#     #         height=1500,
#     #         legend=dict(
#     #             # title=dict(text='flag_pareto'),
#     #             tracegroupgap=0
#     #         )
#     #     )
#
#     #     return st.plotly_chart(fig, on_select='rerun', key='scatter_' + str(self.scatter_count))
#
#     def plot_Jcurb(self, df_cost, X_axis, Y_axis, X_range, Y_range, target_cost=None, fix_cost=None, study_id=None):
#         self.Jcurb_count += 1
#         df_cost['color'] = df_cost['legend'].map({'with_items': 'blue', 'surrogate_estimated': 'orange'})
#         df_cost['symbol'] = df_cost['legend'].map({'with_items': 'circle', 'surrogate_estimated': 'cross'})
#         estimated_x_value = df_cost[df_cost['legend']=='surrogate_estimated'][X_axis].tolist()[0]
#         estimated_y_value = df_cost[df_cost['legend']=='surrogate_estimated'][Y_axis].tolist()[0]
#         #X_range should be updated when there is fix_cost
#         if fix_cost is not None:
#             X_range[0] = X_range[0]-(X_range[1]-X_range[0])/10*3
#
#         fig = px.scatter(
#             df_cost,
#             x=X_axis,
#             y=Y_axis,
#             range_x=X_range,
#             range_y=Y_range,
#             color='legend',
#             symbol='legend',
#             color_discrete_map={'with_items': 'blue', 'surrogate_estimated': 'orange', study_id:'purple'},
#             symbol_map={'with_items': 'circle', 'surrogate_estimated': 'cross', study_id:'star'}
#         )
#         fig.update_traces(marker=dict(size=20))
#         fig.update_layout(width=800, height=800,
#                         autosize=False,
#                           )
#         #目標コスト表示機能
#         if target_cost is not None:
#             fig.add_shape(
#                 type = 'line',
#                 x0 = min(X_range),
#                 x1 = max(X_range),
#                 y0 = target_cost,
#                 y1 = target_cost,
#                 line = dict(color='red', width=2, dash = 'dash')
#             )
#
#         if fix_cost is not None:
#             fig.add_shape(
#                 type='rect',
#                 x0 = estimated_x_value - (X_range[1]-X_range[0])/10*2,
#                 x1 = estimated_x_value - (X_range[1]-X_range[0])/10*1,
#                 y0 = Y_range[0],
#                 # y1 = estimated_y_value,
#                 y1 = fix_cost,
#                 line=dict(
#                     color='RoyalBlue',
#                     width=2,
#                 ),
#                 fillcolor='LightSkyBlue'
#             )
#             fig.add_trace(go.Scatter(
#                 x=[estimated_x_value - (X_range[1]-X_range[0])/10*1.5],
#                 # y=[estimated_y_value+ (Y_range[1]-Y_range[0])/20],
#                 y=[fix_cost+ (Y_range[1]-Y_range[0])/20],
#                 text=['初期提案費'],
#                 mode='text'
#             ))
#         print(fig)
#         return st.plotly_chart(fig, on_select='rerun', key='Jcurb_' + str(self.Jcurb_count), use_container_width=False)
#
#     def plot_parallel_coordinate(self, df_sampling, selected_cols):
#         #別の方法試す　6/17
#         dimentions = list([dict(range=[df_sampling[col].min(), df_sampling[col].max()], label=col, values=df_sampling[col]) for col in selected_cols])
#         fig = go.FigureWidget(data=go.Parcoords(dimensions=dimentions))
#
#         self.parallel_coordinate_count += 1
#         # fig = px.parallel_coordinates(df_sampling[selected_cols])
#         return st.plotly_chart(fig, on_select='rerun',selection_mode='lasso', key='parallel_coordinate_' + str(self.parallel_coordinate_count)), fig
#
# def mark_pareto(df_sampling, X_axis, X_condition, Y_axis, Y_condition):
#     #this function should mark pareto for only rows that flag_pareto is None
#     df_sampling = df_sampling.sort_values(by=Y_axis,ascending=(Y_condition=='最小化'))
#     df_sampling = df_sampling.sort_values(by=X_axis,ascending=(X_condition=='最小化'))
#     df_sampling['flag_pareto'].fillna(True, inplace=True)
#     if Y_condition == '最小化':
#         # Y_compared = df_sampling[Y_axis].iat[0]
#         Y_compared = 9999999999
#     else:
#         #Y_compared = df_sampling[Y_axis].iat[-1]
#         Y_compared = -9999999999
#
#     #処理対象のデータが多すぎる、最初の比較対象以上/以下のデータはドロップできないか
#     if Y_condition == '最小化':
#         df_sampling_remain = df_sampling.loc[(df_sampling[Y_axis]<=Y_compared) & (df_sampling['flag_pareto']==True)]
#         df_sampling.loc[(df_sampling[Y_axis]>Y_compared) & (df_sampling['flag_pareto']==True), 'flag_pareto'] = False
#         Y_compared+=1
#     else:
#         df_sampling_remain = df_sampling.loc[(df_sampling[Y_axis]>=Y_compared) & (df_sampling['flag_pareto']==True)]
#         df_sampling.loc[(df_sampling[Y_axis]<Y_compared) & (df_sampling['flag_pareto']==True), 'flag_pareto'] = False
#         Y_compared-=1
#
#     for i, row in df_sampling_remain.iterrows():
#         if (Y_condition=='最小化' and row[Y_axis] < Y_compared) or (Y_condition=='最大化' and row[Y_axis] > Y_compared):
#             Y_compared = row[Y_axis]
#         else:
#             row.loc['flag_pareto']=False
#             df_sampling.loc[df_sampling['<ID>']==row['<ID>'],'flag_pareto']=False
#
#     #基点の行は基点用のフラグで上書き
#     #この機能はこの関数で持つべき機能ではないため無効化 8/4
#     # df_base = df_sampling[]
#     # df_sampling.loc[df_sampling['<ID>']==base_id, 'flag_pareto'] = 'Base'
#     # df_sampling[df_sampling['<ID>']==base_id] = df_base
#
#     return df_sampling
#
# def mark_satisfied(df_sampling, X_axis, X_condition, X_target, Y_axis, Y_condition):
#     #mark_pareto終わった時点でソートはできている想定
#
#     if X_condition == '最大化':
#         df_satisfied_pareto = df_sampling.loc[(df_sampling[X_axis]>=float(X_target))&(df_sampling['flag_pareto'])]
#     else:
#         df_satisfied_pareto = df_sampling.loc[(df_sampling[X_axis]<=float(X_target))&(df_sampling['flag_pareto'])]
#     if len(df_satisfied_pareto)>=1:
#         df_satisfied_pareto = df_satisfied_pareto.iloc[-1]
#     if len(df_satisfied_pareto) >= 1:
#         df_sampling.loc[df_sampling['<ID>']==df_satisfied_pareto['<ID>'], 'flag_pareto'] = 'Satisfied'
#
#     return df_sampling
#
# def is_num_delimiter(s):
#     try:
#         float(s.replace(',', ''))
#     except ValueError:
#         return False
#     else:
#         return True
#
#
#
# def go_compare_base_and_seledted():
#     cellStyle_by_base_comparison=JsCode("""
#             function (params){
#                 console.log(params);
#                 if (params.value === '+'){
#                     return {"background-color": "#FA8072"};
#                 } else if (params.value === '-'){
#                     return {"background-color": "#8FD3FE"};
#                 }
#             }
#         """)
#
#     go = {
#         'columnDefs':[
#             {
#                 'headerName':'パラメータ',
#                 'field':'parameter',
#             },
#             {
#                 'headerName':'基点',
#                 'field':'base',
#                 'cellDataType': 'Text'
#             },
#             {
#                 'headerName':'→',
#                 'field':'how',
#                 'cellStyle':cellStyle_by_base_comparison
#             },
#             {
#                 'headerName':'選択点',
#                 'field':'changed',
#                 'cellDataType': 'Text'
#             }
#         ],
#         'defaultColDef':{
#             'resizable': True,
#         }
#     }
#     return go
#
# def init_session_state():
#     st.session_state.df_sampling = None
#     st.session_state.X_axis_before = None
#     st.session_state.Y_axis_before = None
#     st.session_state.X_condition_before = None
#     st.session_state.Y_condition_before = None
#     st.session_state.X_target_before = None
#     st.session_state.Y_target_before = None
#     st.session_state.X_or_Y_and_Cost = None
#     st.session_state.df_cost_performance = None
#     st.session_state.df_cost = None
#     st.session_state.df_cost_updated = None
#     st.session_state.cost_updated = False
#     st.session_state.df_estimated_plot = None
#     st.session_state.selected_surrogate_inputs = None
#     st.session_state.surrogate_model_slider_iterator = 0 #サロゲートモデルスライダーは、初期値スタディが変わるたびにリセットのため作り直す必要があり、その時にkeyを変える必要がある。この変数は初期値変更のたびに数値がふえることで、毎回keyが変えられる
#
# def get_sampling(project_ids, phase_ids):
#     df_sampling_path = sql.get_sampling_path(project_ids, phase_ids)
#     if len(df_sampling_path)>0:
#         sampling_path =df_sampling_path['sampling_data_path'].tolist()[0]
#     else:
#         return None
#     df_sampling = pd.read_excel(sampling_path)
#     # st.write(df_sampling)
#     #modeFRONTIERサンプリング情報の列名にはいつもなぜか空白が入っているため取り除く
#     df_sampling.columns = [x.replace(' ','') for x in df_sampling.columns]
#     return df_sampling
#
# def get_cost(project_ids):#複数プロジェクトに対応させる。 7/4j
#
#     df_cost = sql.get_cost_view(project_ids)
#     df_cost.rename(columns={'cost_item_id':'id', 'item_name_4':'part_name','effect':'parameter_change_amount','cost':'cost_change_amount'}, inplace=True)
#     # df_cost = df_cost[['project_id','id', 'part_name', 'parameter_name', 'parameter_change_amount', 'cost_change_amount']]
#     return df_cost
#
# def process_cost(df_sampling, df_cost, df_base):
#
#     # st.write('df_cost')
#     #先にパラメータ名ごとにテーブルを分けて辞書管理する
#     dict_df_cost = {}
#     for parameter in  list(set(df_cost['parameter_name'].tolist())):
#         dict_df_cost[parameter] = df_cost[df_cost['parameter_name']==parameter] #コスト情報前処理で、コスパ順並べ替え
#         dict_df_cost[parameter]['cost_performance'] =  -dict_df_cost[parameter]['cost_change_amount'] / dict_df_cost[parameter]['parameter_change_amount']
#         dict_df_cost[parameter] = dict_df_cost[parameter].sort_values(by='cost_performance')
#         dict_df_cost[parameter]['parameter_change_accumulate'] = dict_df_cost[parameter]['parameter_change_amount'].cumsum(axis=0)
#         dict_df_cost[parameter]['cost_change_accumulate'] = dict_df_cost[parameter]['cost_change_amount'].cumsum(axis=0)
#         dict_df_cost[parameter]['part_name_accumulate'] = ['|'.join(dict_df_cost[parameter]['part_name'][:i+1].tolist()) for i in range(len(dict_df_cost[parameter]['part_name']))]
#     #基点-各サンプリングでΔCd算出、その大きさによってΔコストをつける
#     #ここで各コスト情報ごとにのループが発生する
#     for parameter in list(set(df_cost['parameter_name'].tolist())):
#         #コスト情報にあるパラメータがサンプリングデータになければ、Δパラメータは計算しない　　山口7/8
#         if not parameter in df_sampling.columns:
#             continue
#         delta_variable= df_sampling[parameter] - df_base[parameter].tolist()[0]
#         df_sampling['delta_'+parameter] = delta_variable
#         # st.write(df_sampling.columns)
#     for parameter in list(set(df_cost['parameter_name'].tolist())):
#         #コスト情報にあるパラメータがサンプリングデータになければ、Δパラメータは計算しない　　山口7/8
#         if not parameter in df_sampling.columns:
#             continue
#         df_cost = dict_df_cost[parameter]
#         df_sampling[['delta_'+parameter + '_cost', parameter+'_item_name']] =df_sampling.apply(lambda row: calc_delta_cost(df_cost, parameter, row['delta_' + parameter]), axis=1, result_type='expand')
#     #すべてのコストの合算を出す
#     df_sampling['total_cost'] = df_sampling.loc[:,df_sampling.columns.str.contains('cost')].sum(axis=1)
#
#     def join_item_name_col(row):
#         return '|'.join(row[filter(lambda col: '_item_name' in col, df_sampling.columns)])
#     #すべてのアイテム名をタス
#     df_sampling['all_names'] = df_sampling.apply(join_item_name_col,axis=1)
#
#     return df_sampling
#
# class Rsm :
#     def __init__(self):
#         self.rsm_file_path = ''
#         self.rsm_macro = ''
#         self.df_surrogate_model_path = None
#         self.df_surrogate_model_view =None
#         self.x1 = None
#         self.wb = None
#         self.ws = None
#
#     def get_df_surrogate_model_view(self):
#         return self.df_surrogate_model_view
#
#     def get_rsm(self, project_ids, phase_ids): # 1prjに複数サロゲートモデル紐づいているときに対応させるようにする 7/28
#         #複数プロジェクトに対応させる7/4
#
#         self.df_surrogate_model_view = sql.get_surrogate_model_view(project_ids, phase_ids)
#         if len(self.df_surrogate_model_view)==0:
#             return False, False
#         # self.input_cols = ['A','Battセル数', 'Cd','Frギア比','IpRank','RRC'] #RSMの入力変数列は、RSMを取得すればわかるようにする この宣言をなくして、必要になったときにdf_surrogate_model_viewからとるようにする
#         # self.output_cols = ['燃費'] #RSMの出力変数列は、RSMを取得すればわかるようにする この宣言をなくして、必要になったときにdf_surrogate_model_viewからとるようにする
#
#
#         # return self.rsm_file_path, self.rsm_macro
#         return self.df_surrogate_model_view
#
#     def get_surrogate_model_min_max(self):#self.df_surrogate_model_viewから、各サロゲートモデルの入力変数の最小値、最大値を取得する
#         if self.df_surrogate_model_view is None:
#             raise ValueError("Surrogate model view data is not initialized. Please call get_rsm() first.")
#
#         df_min_max = self.df_surrogate_model_view.groupby('input_parameter_name').agg({'min_input': 'min', 'max_input': 'max'}).reset_index()
#         return df_min_max
#
#     def open_excel(self, df_surrogate_model_path_one_row):
#         self.rsm_file_path = df_surrogate_model_path_one_row['surrogate_model_path']
#         self.rsm_macro = df_surrogate_model_path_one_row['macro']
#         print('coinitialize')
#         pythoncom.CoInitialize()
#         print('dispatch')
#         self.x1 = win32com.client.DispatchEx('Excel.Application') # to prevent error that caused by Dispatching more than twice, use EnsureDispatch instead of Dispatch
#         self.x1.Visible = False
#         print('get wb')
#         self.wb = self.x1.Workbooks.Open(os.path.abspath(self.rsm_file_path)) #相対パスではいけない
#         # self.x1.Visible = Faｊｊｊ
#         print('get ws')
#         self.ws = self.wb.Worksheets(1)
#
#     def estimate(self, inputs, input_cols):
#         end_col = self.number_to_excel_column(len(inputs))
#         # for i, value in enumerate(inputs):
#         #     self.ws.cells(6,i+1).Value = value
#         #     self.ws.cells(5,i+1).value = input_cols[i]
#
#         self.ws.Range('A6:'+end_col+'6').Value = inputs
#         self.ws.Range('A5:'+end_col+'5').Value = input_cols
#
#
#         rng_inputs = self.ws.Range('A6:'+end_col+'6')
#         rng_input_cols = self.ws.Range('A5:'+end_col+'5')
#
#
#         estimate = self.x1.Application.Run(self.rsm_macro,rng_inputs, rng_input_cols)
#
#         return estimate
#
#     def number_to_excel_column(self,n):
#         result = ''
#         while n > 0:
#             n, remainder = divmod(n - 1, 26)
#             result = chr(65 + remainder) + result
#         return result
#
#     def close_excel(self):
#         try:
#             if self.wb is not None:
#                 self.wb.Close(SaveChanges=False)
#             if self.x1 is not None:
#                 self.x1.Quit()
#         except Exception as e:
#             st.exception(e)
#         self.ws = None
#         self.wb = None
#         self.x1 = None
#
#     def estimate_plot(self, dict_inputs, project_ids, phase_ids):
#         print("********************")
#         print("***estimate_plot****")
#         print("********************")
#         list_by_project_phase_id = [group_df for _, group_df in self.df_surrogate_model_view.groupby(['project_id', 'phase_id']) ]
#         for i, df_surrogate_model_view_by_project_phase_id in enumerate(list_by_project_phase_id):
#             list_by_output_id = [group_df for _, group_df in df_surrogate_model_view_by_project_phase_id.groupby(['output_surrogate_model_parameter_id'])]#選択したプロジェクト、フェーズに紐づくサロゲートモデルごとにDFを分けるj
#             dict_inputs_outputs = dict_inputs
#             for i, df_surrogate_model_view_by_project_phase_output_id in enumerate(list_by_output_id):
#                 onerow = df_surrogate_model_view_by_project_phase_output_id.iloc[0]
#                 input_cols =list(set(df_surrogate_model_view_by_project_phase_output_id['input_parameter_name'].tolist()))
#                 output_parameter = df_surrogate_model_view_by_project_phase_output_id['output_parameter_name'].tolist()[0]
#                 print('go open excel')
#                 try:
#                     self.open_excel(onerow) #今のループの行を渡して動作するようにする7/4
#                     print('excel opened')
#                     dict_inputs_outputs[output_parameter] = self.estimate(list(dict_inputs.values()), list(dict_inputs.keys()))
#                     self.close_excel()
#                 except Exception as e:
#                     kill_excel()
#                     self.close_excel()
#                     raise e
#         ######調整　すぐに消す
#
#         dict_inputs_outputs['燃費'] = self.put_bias_by_cell(dict_inputs_outputs['Battセル数'],'燃費',dict_inputs_outputs['燃費'])
#         dict_inputs_outputs['time0_100'] = self.put_bias_by_cell(dict_inputs_outputs['Battセル数'],'time0_100',dict_inputs_outputs['time0_100'], dict_inputs_outputs['FrMG最大トルク'])
#
#
#         return dict_inputs_outputs
#
#     ##結果調整用関数すぐに消す
#     def put_bias_by_cell(self, CellNum, performance_name, performance, FrMaxTrq=None):
#         print(performance_name)
#         print(performance)
#         print(CellNum)
#         if performance_name=='燃費':
#             biased_performance = performance-performance*(0.059-(-0.00003125*CellNum*CellNum+0.0055*CellNum-0.24))
#         elif performance_name=='time0_100':
#             biased_performance = performance+performance*(0.153+(0.00046875*CellNum*CellNum-0.083125*CellNum+3.66)+(-0.001142857*FrMaxTrq+0.36))
#         print(biased_performance)
#         return biased_performance
#
#     #     return df_cost_performance
#     def add_cost_performance_info(self, df_cost, df_base, project_info):#複数プロジェクトのコストに対応
#         print("*******************************")
#         print("***add_cost_performace_info****")
#         print("*******************************")
#         #df_surrogate_model_pathのproject_id, phase_id の組み合わせの数でルーぷ
#         #サロゲートモデルの数だけループするようにする
#         df_cost_performance = None
#         list_by_project_phase_id = [group_df for _, group_df in self.df_surrogate_model_view.groupby(['project_id', 'phase_id']) ]
#
#         # for i, row in self.df_surrogate_model_path.iterrows():
#         for i, df_surrogate_model_view_by_project_phase_id in enumerate(list_by_project_phase_id):
#             list_by_output_id = [group_df for _, group_df in df_surrogate_model_view_by_project_phase_id.groupby(['output_surrogate_model_parameter_id'])]
#             row = df_surrogate_model_view_by_project_phase_id.iloc[0]
#             df_cost_one_proj = df_cost[df_cost['project_id']==row['project_id']]
#             # no_change_row = [[df_cost_one_proj['project_id'].tolist()[0],0, '', 'Cd', 0, 0]]
#             df_no_change_row = df_cost_one_proj.iloc[[0]].copy()
#             df_no_change_row['id'] = 0
#             df_no_change_row['part_name'] = ''
#             df_no_change_row['parameter_name'] = ''
#             df_no_change_row['parameter_change_amount'] = 0
#             df_no_change_row['cost_change_amount'] = 0
#             df_no_change_row['original_cost'] = 0
#             df_cost_one_proj = pd.concat([df_no_change_row,df_cost_one_proj], axis=0, ignore_index=True)
#             df_cost_one_proj['phase_id'] = row['phase_id']
#             #1　各アイテム単体ごとの燃費を基点に反映させて、燃費向上分を出す
#             #2　燃費/コスト順の高い順で並べなおす
#             #3　各アイテム積算出燃費を出す
#             each_item_performances = []
#             #サロゲートモデルの中から燃費アウトプットのものを取り出す
#             df_surrogate_model_view_for_sorting = next(df for df in list_by_output_id if df['output_parameter_name'].tolist()[0]=='燃費')
#             onerow = df_surrogate_model_view_for_sorting.iloc[0]
#             input_cols = list(set(df_surrogate_model_view_for_sorting['input_parameter_name'].tolist()))
#             try:
#                 self.open_excel(onerow) #今のループの行を渡して動作するようにする7/4
#                 print('excel opened')
#                 #df_base自身の燃費値とdf_baseをサロゲートモデルに通したときの値が違うためＪカーブがゆがんだ、最初にdf_baseをestimateで定義する
#                 df_base_one_item = df_base.copy()
#                 df_base_one_item['燃費'] = self.estimate(df_base_one_item[input_cols].iloc[0].tolist(), input_cols)
#                 for i, cost_row in df_cost_one_proj.iterrows():
#                     #コストアイテムの性能が燃費であったら、サロゲートも出るを通した計算をせずに直接燃費をいじる8/1
#                     if cost_row['parameter_name'] =='燃費':
#                         one_item_performance = df_base_one_item['燃費'] + cost_row['parameter_change_amount']
#                         one_item_performance = one_item_performance.tolist()[0]
#                     else:
#                     #コスト情報にあるパラメータがサンプリングデータになければ、変変更しないまままま計算する山口7/8
#                         if cost_row['parameter_name'] in df_base.columns:
#                             df_base_one_item[cost_row['parameter_name']]= df_base_one_item[cost_row['parameter_name']] + cost_row['parameter_change_amount']
#                         print('go open excel')
#                         one_item_performance = self.estimate(df_base_one_item[input_cols].iloc[0].tolist(), input_cols)
#                     each_item_performances.append(one_item_performance)
#                 self.close_excel()
#             except Exception as e:
#                 kill_excel()
#                 self.close_excel()
#                 raise e
#             df_cost_one_proj['one_item_performance'] = pd.DataFrame({'one_item_performance':each_item_performances})
#             df_cost_one_proj['one_item_performance_change'] = df_cost_one_proj['one_item_performance']-df_cost_one_proj[df_cost_one_proj['id']==0]['one_item_performance'].tolist()[0]
#             #ここでコストが0の時、パフォーマンスが0の時を考慮できていなかったので、ごく微量の下駄をはかせる
#             df_cost_one_proj['one_item_performance_change_per_cost'] = (df_cost_one_proj['cost_change_amount']+0.00001)/(df_cost_one_proj['one_item_performance']-df_cost_one_proj[df_cost_one_proj['id']==0]['one_item_performance'].tolist()[0]+0.00001)
#             df_tmp = df_cost_one_proj[df_cost_one_proj['id']==0] # 基点情報を絶対に一番上に持ってくるため一度抽出
#             df_cost_one_proj = df_cost_one_proj[df_cost_one_proj['id']!=0]# 基点情報を抜き出したので消しておく
#             df_cost_one_proj = df_cost_one_proj.sort_values(by='one_item_performance_change_per_cost',ascending=True)
#             df_cost_one_proj = pd.concat([df_tmp,df_cost_one_proj],axis=0) # concatで基点情報を一番上に
#             df_cost_one_proj.reset_index(inplace=True)
#             # パーツ名積算
#             df_cost_one_proj['accumulate_part_name'] = df_cost_one_proj.index.to_series().apply(lambda i: '|'.join(df_cost_one_proj.loc[:i, 'part_name']))
#
#             for input in input_cols:
#                     df_cost_one_proj[input] = df_base[input].tolist()[0]
#
#             df_cost_one_proj['FE_bias'] =0 # 燃費効果が直接書かれたものはその効果の積算列をもって置き、サロゲートで予測値出した後に足しこむ
#             for i,row in df_cost_one_proj.iterrows():
#                 if i == 0:
#                     continue
#                 df_cost_one_proj.loc[i,input_cols] = df_cost_one_proj.loc[i-1,input_cols]
#                 if row['parameter_name'] != '燃費':
#                     df_cost_one_proj.at[i,'FE_bias'] = df_cost_one_proj.at[i-1, 'FE_bias']
#                     #コスト情報にあるパラメータがサンプリングデータになければ、Δパラメータは計算しない　　山口7/8
#                     if not row['parameter_name'] in df_base.columns:
#                         continue
#                     df_cost_one_proj.at[i,row['parameter_name']] = df_cost_one_proj.at[i-1,row['parameter_name']]+row['parameter_change_amount']
#                 else:#燃費の時はFE_biasに足すだけ
#                     df_cost_one_proj.at[i,'FE_bias'] = df_cost_one_proj.at[i-1, 'FE_bias'] + row['parameter_change_amount']
#
#             #あるプロジェクトに複数性能分のサロゲートモデルがあれば、それぞれについて計算し列を追加する 7/29
#             for i, df_surrogate_model_view_by_project_phase_output_id in enumerate(list_by_output_id):
#                 onerow = df_surrogate_model_view_by_project_phase_output_id.iloc[0]
#                 input_cols =list(set(df_surrogate_model_view_by_project_phase_output_id['input_parameter_name'].tolist()))
#                 print('go open excel')
#                 try:
#                     self.open_excel(onerow) #今のループの行を渡して動作するようにする7/4
#                     print('excel opened')
#
#                     df_cost_one_proj['estimated_' + onerow['output_parameter_name']] = df_cost_one_proj.apply(
#                         # lambda row: self.estimate(row[input_cols], input_cols),
#                         #結果調整用すぐに消す
#                         lambda row: self.put_bias_by_cell(row['Battセル数'], onerow['output_parameter_name'], self.estimate(row[input_cols], input_cols), row['FrMG最大トルク'] ),
#                     axis=1
#                 )
#                     self.close_excel()
#                 except Exception as e:
#                     kill_excel()
#                     self.close_excel()
#                     raise e
#
#             #燃費アイテム分を直接たす
#             df_cost_one_proj['estimated_燃費'] = df_cost_one_proj['estimated_燃費'] + df_cost_one_proj['FE_bias']
#
#             df_cost_one_proj['accumulate_cost'] = df_cost_one_proj['cost_change_amount'].cumsum(axis=0)
#             #ループ後のアウトプットを結合
#             if df_cost_performance is None:
#                 df_cost_performance = df_cost_one_proj
#             else:
#                 df_cost_performance = pd.concat([df_cost_performance, df_cost_one_proj])
#
#         df_cost_performance = pd.merge(df_cost_performance, project_info[['project_id','phase_id','project_info_str']],on=['project_id','phase_id'])
#         return df_cost_performance
#
# def get_preferable_range(df_data, target_cost=None, fix_cost=None):
#     X_max = df_data.max()
#     X_min = df_data.min()
#     if target_cost is not None:
#         X_max = max([X_max, target_cost])
#         X_min = min([X_min, target_cost])
#     if fix_cost is not None:
#         X_max = max([X_max, fix_cost])
#         X_min = min([X_min, fix_cost])
#     X_delta = X_max - X_min
#     X_range = [X_min-X_delta*0.1, X_max+X_delta*0.1]
#     return X_range
#
# #stupid me just defined function that already exist
# # Ha-san added 0214:
# def get_session_choices(choice_number):
#     searching_input_keys = ['architecture_name']
#     searching_input_values = []
#     is_enough_input = True
#
#     for selection_id in range(1, choice_number + 1):
#         selection_name = f"selectoption{selection_id}"
#         searching_input_keys.append(selection_name)
#
#     for key in searching_input_keys:
#         if key in st.session_state:
#             # st.write(f" {key}: {st.session_state[key]}")
#             searching_input_values.append(st.session_state[key])
#         else:
#             is_enough_input = False
#
#     return searching_input_values, is_enough_input
#
# def Jcurb_tab():
#     if 'Jcurb_page_id' not in st.session_state:
#         st.session_state.Jcurb_page_id = 1
#     if not st.session_state.cost_updated:
#         Jcurb_page_id  = stx.tab_bar(data=[
#         # stx.TabBarItemData(id=1, title="Jカーブ", description=None),
#         stx.TabBarItemData(id=2, title="プロジェクト-コスト表", description=None),#プロジェクトに紐づくコスト表示用タブ追加
#         stx.TabBarItemData(id=3, title='サンプリング表示', description=None),
#         # stx.TabBarItemData(id=4, title='コストアイテム表', description=None), #コストアイテム自身の表示用タブ
#         ],default=3)
#     else:
#         Jcurb_page_id  = stx.tab_bar(data=[
#         # stx.TabBarItemData(id=1, title="Jカーブ", description=None),
#         stx.TabBarItemData(id=2, title="プロジェクト-コスト表", description=None),
#         stx.TabBarItemData(id=3, title='サンプリング表示', description=None),
#         # stx.TabBarItemData(id=4, title='コストアイテム表', description=None), #コストアイテム自身の表示用タブ
#         ],default=st.session_state.Jcurb_page_id)
#         st.session_state.cost_updated=False
#
#     return Jcurb_page_id
#
# def add_senario_list_to_sampling(df_sampling):
#         #make it execute no matter flag_senario_toggle is True or False,
#     # if flag_senario_toggle:
#     #シナリオリストデータをst.session_stateに入っているか確認、なければ取らなければいけない
#     df_surrogate_model_parameter = sql.get_surrogate_model_parameter()
#     print('got surrogate model parameter')
#     if 'sim_data_stuck' not in st.session_state or st.session_state.dialog_state:
#         searching_input_sim_values, is_enough_sim_input = get_session_choices(5)
#         df1, df2 = sql.posgre_get_data_sim(*searching_input_sim_values[1:])
#         st.session_state.sim_prj_info_list = df1
#         st.session_state.sim_data_stuck = df2
#     df_list_studies = st.session_state.sim_prj_info_list['study_id']
#     list_studies = df_list_studies.tolist()
#     print('got sim_data_stuck')
#     #前提値referenced_valueも欲しいよね
#     # list_studies = list_studies + ['前提']
#     # studies_plot_on = [st.checkbox(study_id) for study_id in list_studies]
#     #make it concat all studies for now, and then select which to plot later
#     # with xy_expander:
#     #     studies_plot_on = st.multiselect('仕様表示',list_studies, default=list_studies)
#     # list_studies_to_plot = df_list_studies[df_list_studies.isin(studies_plot_on)].tolist()
#     list_studies_to_plot = list_studies #一旦すべてのstudy_idをプロットするようにする
#     list_studies_to_skip = []
#     #選択されたStudy_IDでループ、必要なDB持ってきてサロゲートモデルパラメータIDでmergeして？？？？
#     sim_data_stuck = st.session_state.sim_data_stuck.copy()
#     # st.write(df_surrogate_model_parameter)
#     df_study_with_model_parameter_stuck = None
#     for i, study_id in enumerate(list_studies_to_plot) :
#
#         df_study_with_study_id = sim_data_stuck.loc[:, sim_data_stuck.columns.str.contains(study_id)]
#         # st.write(df_study_with_study_id)
#         related_model_parameter_id_col = df_study_with_study_id.loc[:, df_study_with_study_id.columns.str.contains('r_m_p_id')].columns[0]
#         value_col = df_study_with_study_id.loc[:, df_study_with_study_id.columns.str.contains(';value;')].columns[0]
#         df_study_with_model_parameter = pd.merge(df_study_with_study_id, df_surrogate_model_parameter, how='inner', left_on=related_model_parameter_id_col, right_on='surrogate_model_parameter_id')
#         # st.write(df_study_with_model_parameter)
#         #ここでdf_study_with_model_parameterに無理やりePTコストをくっつけ8/19
#         senario_parameter_id_col = df_study_with_study_id.loc[:, df_study_with_study_id.columns.str.contains('senario_parameter_id')].columns[0]
#
#
#
#         if not any(df_study_with_study_id[senario_parameter_id_col]==400000):
#             continue
#
#         ePT_cost = df_study_with_study_id[df_study_with_study_id[senario_parameter_id_col]==400000][value_col].tolist()[0]
#         try:
#             df_sample_from_study = pd.DataFrame([df_study_with_model_parameter.set_index('parameter_name')[value_col].to_dict()]).astype(float)
#             #あたらしい行に変換したDFに追加情報
#             df_sample_from_study['flag_pareto'] = study_id
#             df_sample_from_study['<ID>'] = max(df_sampling['<ID>']) + 1
#             df_sample_from_study['from_excel'] = 0 #Excelからのデータではないことを示す
#             try:
#                 df_sample_from_study['accumulate_cost_with_fix'] = float(ePT_cost)
#             except:
#                 print('cost is not number')
#                 df_sample_from_study['accumulate_cost_with_fix'] = None
#             df_sampling = pd.concat([df_sampling, df_sample_from_study], ignore_index=True)
#         except ValueError:
#             st.warning(study_id + 'には数字以外の文字が入っているため、プロットをスキップします。')
#             list_studies_to_skip.append(study_id)
#         #df_study_with_model_parameterは舞ループ時に更新されるので、最後のスタディ次第で必要な変数がなかったりする、それを回避するため、毎ループ結果はconcatし、最後に重複を消す
#         df_study_with_model_parameter.columns = [colname.split(';')[1] if ';' in colname else colname for colname in df_study_with_model_parameter.columns ]
#         if df_study_with_model_parameter_stuck is None:
#             df_study_with_model_parameter_stuck = df_study_with_model_parameter
#         else:
#             df_study_with_model_parameter_stuck = pd.concat([df_study_with_model_parameter_stuck,df_study_with_model_parameter])
#     list_studies_to_plot = [study_id for study_id in list_studies_to_plot if study_id not in list_studies_to_skip]
#     df_study_with_model_parameter_stuck.drop_duplicates(subset=['senario_parameter_id'], inplace=True)
#     # st.write(df_study_with_model_parameter_stuck)
#     return df_sampling, df_list_studies, df_study_with_model_parameter_stuck, list_studies_to_plot
#
# def XY_settings(df_sampling, df_list_studies, list_studies_to_plot, df_study_with_model_parameter):
#     st.subheader('X&Yセッティング')
#     with st.container():
#         xy_expander = st.expander('XY軸設定', expanded=False) #XY軸設定のexpanderを作成
#         with xy_expander:
#             settingcol1_1, settingcol1_2 = st.columns([1,1])
#             with settingcol1_1:
#                 #####プロットに表示するデータ種別を制御するトグル  excel_sampling フラグによって消す
#                 flag_senario_toggle = st.toggle("Sim管理表連携", value=True)
#                 flag_sampling_display = st.toggle("サンプリングデータ表示")
#                 if flag_senario_toggle and flag_sampling_display:
#                     sampling_columns = df_sampling.columns.tolist()
#                 elif flag_senario_toggle and not flag_sampling_display:
#                     sampling_columns = df_sampling[df_sampling['from_excel']==0].dropna(axis=1).columns.tolist()
#                 elif not flag_senario_toggle and flag_sampling_display:
#                     sampling_columns = df_sampling[df_sampling['from_excel']==1].dropna(axis=1).columns.tolist() #シナリオ連携をOFFにした場合、サンプリングデータはExcelからのものだけを表示する
#                 else:
#                     st.error('表示するアイテムがありません')
#                     return
#                 X_default_option_index = sampling_columns.index('time0_100')#TODO仕向けによって変えるように
#                 Y_default_option_index = sampling_columns.index('燃費')#TODOアーキによって変わるように
#                 X_axis = st.selectbox('X軸選択', sampling_columns, index=X_default_option_index)
#                 Y_axis = st.selectbox('Y軸選択', sampling_columns, index=Y_default_option_index)
#                 Cost_axis = 'total_cost'
#                 X_or_Y_and_Cost = X_axis
#                 # X_target = st.text_input('X軸 要求値') 機能ガン積でわけわからないためいったん無効化 8/4
#                 #Y_target = st.text_input('Y軸 要求値') #現在用途なし
#                 X_target = None
#
#             with settingcol1_2:
#                 if flag_sampling_display:
#                     X_condition = st.radio('', ['最大化','最小化'], key = 'condition_1')
#                     Y_condition = st.radio('', ['最大化','最小化'], key = 'condition_2')
#                 else:
#                     X_condition = '最大化'
#                     Y_condition = '最大化'
#                 Cost_condition = '最小化'
#             studies_plot_on = st.multiselect('仕様表示',list_studies_to_plot, default=list_studies_to_plot)
#             list_studies_to_plot = df_list_studies[df_list_studies.isin(studies_plot_on)].tolist()
#             ##要求線設定
#             option_line_plot_parameter = [X_axis, Y_axis]
#             st.subheader('要求線表示') # make it kanji
#             flags_line_plot_parameter = [st.checkbox(parameter_name, value=True) for parameter_name in option_line_plot_parameter]
#             line_plot_list = [item for item, flag in zip(option_line_plot_parameter, flags_line_plot_parameter) if flag]
#         #     line_plot_list = st.multiselect('制約線表示', option_line_plot_parameter,['燃費','time0_100'])
#             # st.write(df_study_with_model_parameter)
#             df_referenced_value_and_name = df_study_with_model_parameter.loc[:,df_study_with_model_parameter.columns.str.contains('referenced_value|parameter_name|value')] #referenced_value列は一列あればよい
#
#             df_line_plot = df_referenced_value_and_name[df_referenced_value_and_name['parameter_name'].isin(line_plot_list)].loc[:,df_referenced_value_and_name.columns.str.contains('referenced_value|parameter_name')]
#             # st.write(df_line_plot)
#             df_line_plot.columns = ['parameter_name_1','parameter_name_2','referenced_value', 'parameter_name']
#
#     return flag_senario_toggle, flag_sampling_display, sampling_columns, X_default_option_index, Y_default_option_index, X_axis, Y_axis, Cost_axis, X_or_Y_and_Cost, X_target, X_condition, Y_condition, list_studies_to_plot, df_line_plot
#
# def Jcurb_setting(list_project_info_str, list_studies_to_plot):
#     st.subheader('Jカーブセッティング')
#     Jcurb_expander = st.expander('Jカーブ表示', expanded=False) #Jカーブ表示のexpanderを作成
#     with Jcurb_expander:
#         with st.container():
#             project_info_visible = [st.checkbox(prj_str, value=True) for prj_str in list_project_info_str]
#             settingcol2_1, settingcol2_2 = st.columns([1,1])
#             with settingcol2_1: #SiSiCスイッチの追加
#                 study_id_plot_on_Jcurb = st.multiselect('Jカーブ上に表示する仕様', list_studies_to_plot, default=list_studies_to_plot[0])
#
#
#             with settingcol2_2: #仮置きでコスト基点場所 TODO 固定費どこに保存する?
#                 fix_cost = st.text_input('初期提案費', value=690000)
#                 target_cost = st.text_input('コスト目標', value = 657000)
#
#     return study_id_plot_on_Jcurb, fix_cost, target_cost
#
# def const_and_sliders(rsm, df_sampling, flag_senario_toggle, list_studies_to_plot, project_ids, phase_ids):
#     default_slider_input_col = rsm.get_df_surrogate_model_view()['input_parameter_name'].drop_duplicates().tolist()
#     default_slider_output_col = rsm.get_df_surrogate_model_view()['output_parameter_name'].drop_duplicates().tolist()
#
#     default_slider_col = default_slider_input_col + default_slider_output_col
#
#     graphcol3sub1, graphcol3sub2, graphcol3sub3= st.columns([2,1,1])
#     with graphcol3sub1:
#         st.subheader('スライダー表示列')
#     selected_columns = st.multiselect('', default_slider_col, default=default_slider_col )
#     selected_columns_constraint = {}
#     with graphcol3sub2:
#         with st.popover('制約情報',use_container_width=True):
#             #制約理由を画像で表示させる
#             st.subheader('制約理由')
#             #TODO Imageはアップロードさせる？
#             image_path = './uploaded_files/images/aa.png'
#             image = Image.open(os.path.abspath(image_path))
#             st.image(image )
#
#
#             #選択されたパラメに対して最大値最入力させる
#             #TODO 最大値最小値はデータベース管理し、いつでも保存、参照できる状態にする
#             # maxcol = {}
#             # mincol = {}
#             default_consts = {
#                 'A0':[154.6,154.6],
#                 'A1':[-0.282, -0.282],
#                 'A2':[0.0514, 0.0514],
#                 'IpRank':[1970,1970],
#                 'FrMG最大トルク':[315,315],
#                 'Frギア比':[8.386,9],
#                 'Battセル数':[81,96]
#             }
#             with st.expander('制約数値'):
#
#                     # constcol1, constcol2 = st.columns([1,1])
#
#                     for i, column in enumerate(selected_columns):
#                         # mincol[column], maxcol[column] = st.columns([1,1])
#                         default_const = default_consts.get(column)
#                         if default_const is not None:
#                             default_max_const = default_const[1]
#                             default_min_const = default_const[0]
#                         else:
#                             default_max_const = df_sampling[column].min()
#                             default_min_const = df_sampling[column].max()
#                         minconst = df_sampling[column].min()
#                         maxconst = df_sampling[column].max()
#                         st.subheader(column)
#                         # with constcol1:
#                         minconst = st.text_input('最小値', value=default_min_const, key='min_const_' + column)
#                         # with maxcol[column]:
#                         # with constcol2:
#                         maxconst = st.text_input('最大値', value=default_max_const, key='max_const_' + column)
#                         # with mincol[column]:
#                         selected_columns_constraint[column] =[minconst, maxconst]
#
#
#     with graphcol3sub3:
#         flag_apply_constraint = st.toggle('制約反映')
#
#
#
#     #やっぱりparallel coordinate 動かしたい やっぱり駄目でした6/17
#     # parallel_event, fig = plotter.plot_parallel_coordinate(df_sampling, selected_columns)
#     # st.write(parallel_event, fig.data[0])
#
#     selected_columns_ranges = []
#     with st.popover('範囲スライダー(MinMax定義)',use_container_width=True):
#         with st.form(' '):
#             submitted = st.form_submit_button('反映')
#             for i, cols in enumerate(selected_columns):
#                 min_value = [float(selected_columns_constraint[cols][0]) if flag_apply_constraint else df_sampling[cols].min()][0]
#                 max_value = [float(selected_columns_constraint[cols][1]) if flag_apply_constraint else df_sampling[cols].max()][0]
#                 selected_columns_ranges.append(st.slider(cols + 'の範囲',
#                                                         min_value=df_sampling[cols].min()*0.95,
#                                                         max_value=df_sampling[cols].max()*1.05,
#                                                         value=(min_value,max_value )))#min とmanの値が完全一致するとエラーになるため少しだけ下駄を付ける
#                 # if df_sampling_filtered is None:
#                 df_sampling_filtered = df_sampling[(df_sampling[cols] >= selected_columns_ranges[i][0]) & (df_sampling[cols] <= selected_columns_ranges[i][1])]
#                 # else:
#                     # df_sampling_filtered = df_sampling_filtered[(df_sampling_filtered[cols] >= selected_columns_ranges[i][0]) & (df_sampling_filtered[cols] <= selected_columns_ranges[i][1])]
#
# ###サロゲートモデル連動機能を付けてみよう
# #スライダーを入力変数の数だけつける
# # その数値でEstimateする
# #Siスイッチを入れる
#     with st.popover('サロゲートモデルスライダー',use_container_width=True):
#         #初期スタディ選択
#         if flag_senario_toggle:
#             # selectable_study_id_for_surrogate_slider = st.session_state.sim_prj_info_list['study_id'].tolist() 選択できるStudy一覧は既に定義済みだｔ選択できるStudy一覧は既に定義済みだったのでコメントアウト
#
#             selected_study_id_for_surrogate_slider = st.selectbox('初期値',list_studies_to_plot)
#         with st.form('   '):
#     # st.subheader('サロゲートモデルスライダー')
#             submitted2 = st.form_submit_button('反映')
#             selected_inputs = {}
#             #サロゲートモデルの最大値最小値値を入手し、スライダーの最大値最小値とする
#             df_min_max = rsm.get_surrogate_model_min_max()#TODO まず一つ プロジェクトにサロ最大値最小値は最大値最小値は共通だとす
#             flag_SiC = st.toggle('SiC', value=True)
#             for i, cols in enumerate(default_slider_input_col):
#                 #初期値あかん
#                 #value初かわかわ初期値選択かわったわったときにやらないとだめ
#                 selected_inputs['study_id'] = selected_study_id_for_surrogate_slider
#                 slider_space_holder = st.empty()
#                 if 'selected_surrogate_inputs' not in st.session_state or st.session_state.selected_surrogate_inputs is None or st.session_state.selected_surrogate_inputs['study_id'] != selected_study_id_for_surrogate_slider:
#                     slider_space_holder.empty()
#                     st.session_state.surrogate_model_slider_iterator += 1
#                 if flag_senario_toggle:
#                     value = df_sampling_filtered[df_sampling_filtered['flag_pareto']==selected_study_id_for_surrogate_slider][cols].tolist()[0]
#                 else:
#                     value = df_min_max[df_min_max['input_parameter_name']==cols]['min_input'].values[0] #サロゲートモデルの最小値を初期値にする
#                 #stepの値は、小数点以下の数値のあたいとする
#                 #TODO 刻みの粗さはパラメータごとに定義しないといけない
#                 precision = float(str('%e' % value).split('e')[1])
#                 if precision >= 0:
#                     step = 0.01
#                 else:
#                     step = 10**(precision-1)
#                 selected_inputs[cols] = slider_space_holder.slider(cols + 'の値', min_value=df_min_max[df_min_max['input_parameter_name']==cols]['min_input'].values[0], max_value=df_min_max[df_min_max['input_parameter_name']==cols]['max_input'].values[0], value=value, step=float(step), key='surrogate_model_slider_' + cols + '_' + str(st.session_state.surrogate_model_slider_iterator) )#,
#             #estimate_plotは入力が変わったら再実行する
#             selected_inputs['flag_SiC'] = flag_SiC
#             if 'selected_surrogate_inputs' not in st.session_state or st.session_state.selected_surrogate_inputs != selected_inputs or selected_inputs != st.session_state.selected_surrogate_inputs:
#                 # st.write('recalc estimate_plot')
#                 estimated_plot = rsm.estimate_plot(selected_inputs.copy(), project_ids, phase_ids)#インプットの辞書を送ったら出力の辞書かえすやつつくる
#                 df_estimated_plot = pd.DataFrame(estimated_plot,index=[0])
#                 df_estimated_plot['flag_pareto'] = 'surrogate_estimated'
#                 #Si直書き
#                 if not flag_SiC:
#                     df_estimated_plot['燃費'] = df_estimated_plot['燃費'] - 0.5 #SiCの時はサロゲートモデルの燃費を0.5下げる
#                 st.session_state.df_estimated_plot = df_estimated_plot
#             else:
#                 df_estimated_plot = st.session_state.df_estimated_plot
#             #estimate_plotはselected_inputsが変わったら再実行するようにするたうにするため、セッションステートに保存しておく
#             # st.session_state.selected_surrogate_inputs = selected_inputs ここで実行するとJカーブ側のプロットアップデートがされなくなるので後回し
#     return selected_inputs, df_estimated_plot, flag_SiC, df_sampling_filtered, default_slider_col
#
# def handle_event_Jcurb(event_Jcurb, df_cost_performance, df_sampling_filtered, default_slider_col):
#     '''
#     Jカーブプロットで選択されたプロットについて詳細のグリッド表示、XYプロットで表示するためのdf_samplingへの情報を行う
#     TODO グリッド表示で見せる行数を絞る
#     '''
#
#     if len(event_Jcurb['selection']['points'])>0:
#             #選択された解の表示用カラム設定
#             #point_index is not always index i wanted, assuming curve_number + point_index is the index of the selected point
#             idx = event_Jcurb['selection']['points'][0]['curve_number'] + event_Jcurb['selection']['points'][0]['point_index']
#             df_selected = pd.DataFrame([df_cost_performance.iloc[idx]])
#             selected_project_id = df_selected['project_id'].tolist()[0]
#             graphcol1_selection,graphcol2_selection, graphcol3_selection = st.columns([4, 4, 3])
#             #praphcol2_selectionｂにアイテム一覧をグリッド表示する
#             with graphcol2_selection:
#                all_names_list = df_selected['accumulate_part_name'].tolist()[0].split('|')
#                all_names_list = [x for x in all_names_list if x != '']
#                df_all_names =pd.DataFrame(all_names_list,columns=['アイテム一覧'])
#                df_all_names['選択'] = False
#                selected_items = st.data_editor(df_all_names,hide_index=True, column_order=['選択','アイテム一覧'])
#                checked_items = selected_items[selected_items['選択']].reset_index(drop=True)
#
#             with graphcol1_selection:
#             #1列目：各項目名
#             #2列目：基点パラメータ
#             #3列目：変化後-基点がプラスであれば'+'、マイナスであれば'-'記号
#             #4列目：変化後パラメータ
#                 df_cost_performance_base = df_cost_performance[(df_cost_performance['id']==0) & (df_cost_performance['project_id']==selected_project_id)]
#
#
#                 df_compare = pd.DataFrame({
#                     'parameter':df_cost_performance_base.columns.tolist(),
#                     'base': df_cost_performance_base.astype(str).values.tolist()[0],
#                     'how': ['' if not is_num_delimiter(str(df_cost_performance_base[col].tolist()[0])) else
#                         '+' if float(df_selected[col].tolist()[0]) - float(df_cost_performance_base[col].tolist()[0])>0 else
#                         '-' if float(df_selected[col].tolist()[0]) - float(df_cost_performance_base[col].tolist()[0])<0 else '='
#                          for col in df_cost_performance_base.columns],
#                     'changed': df_selected.astype(str).values.tolist()[0]
#                 })
#
#                 go = go_compare_base_and_seledted()
#                 if not checked_items.empty:
#                     for selected_item in checked_items['アイテム一覧']:
#                         item_changes = df_cost_performance[df_cost_performance['part_name'] == selected_item]
#                         for _, row in item_changes.iterrows():
#                             parameter = row['parameter_name']
#                             change_amount = row['parameter_change_amount']
#                             cost_change_amount = row['cost_change_amount']
#                             one_item_performance_change = row['one_item_performance_change']
#                             df_compare.loc[df_compare['parameter'] == parameter, f'効果_{selected_item}'] = change_amount
#                             df_compare.loc[df_compare['parameter'] == 'accumulate_item_performance', f'効果_{selected_item}'] = one_item_performance_change
#                             df_compare.loc[df_compare['parameter'] == 'accumulate_cost', f'効果_{selected_item}'] = cost_change_amount
#                         #選択されたアイテムの数だけ列を追加する
#                         go['columnDefs'].append({'headerName':f'効果_{selected_item}', 'field':f'効果_{selected_item}','cellDataType':'Text'})
#                 AgGrid(df_compare, go, allow_unsafe_jscode=True)
#
#             #Jcurbでプロット選択されたらら、それをサンプリング側に反映させる
#             #df_selected.columnsのうちestimated_と含まれている列からestimated_を除く <- 先にもとからある燃費0_100を落とさないと事故る
#
#             df_selected.drop(['燃費', 'time0_100'], axis=1, inplace=True)
#             df_selected.columns = [col.replace('estimated_', '') for col in df_selected.columns]
#             df_selected['flag_pareto'] = 'selected_from_Jcurb'
#             #そうすればconcatできる
#             if not df_sampling_filtered is None:
#                 df_selected['<ID>'] = max(df_sampling_filtered['<ID>']) + 1 #新しいIDを付与する
#                 df_sampling_filtered = pd.concat([df_sampling_filtered, df_selected], ignore_index=True)
#             # else:
#             #     df_selected['<ID>'] = max(df_sampling['<ID>']) + 1 #新しいIDを付与する
#             #     df_sampling = pd.concat([df_sampling, df_selected], ignore_index=True)
#
#             # st.write(df_selected)
#             # st.write(df_sampling_filtered)
#     return df_sampling_filtered
#
# def Jcurb_ui():
#     start = time.time()
#     print('Jcurb_ui')
#        #データイニシャライズ
#
#     project_info = st.session_state.prj_info_list.drop_duplicates(subset=['project_id', 'phase_id'])[['project_id', 'phase_id','project_code', 'architecturename', 'z_destination','z_drive_system', 'z_class_name_get_str']]
#     project_ids = project_info['project_id'].tolist()
#     phase_ids = project_info['phase_id'].tolist()
#     architectures = project_info['architecturename'].tolist()
#     destinations = project_info['z_destination'].tolist()
#     list_project_info_str = [row['project_code'] + '_' + row['z_destination'] + '_' + row['z_drive_system'] + '_' + row['z_class_name_get_str'] + '_' + row['architecturename'] for i, row in project_info.iterrows()]
#     project_info['project_info_str'] = pd.DataFrame(list_project_info_str)
#     if 'jcurb_project_ids_before' not in st.session_state or project_ids != st.session_state.jcurb_project_ids_before or phase_ids != st.session_state.jcurb_phase_ids_before:
#         init_session_state()
#     st.session_state.jcurb_project_ids_before = project_ids
#     st.session_state.jcurb_phase_ids_before = phase_ids
#     print('initialized')
#     print(start - time.time(), 'sec')
#
#     if st.button("戻る"):
#             back_to_SPDM_LIST()
#
#     # base_id = int(st.text_input('基点ID',0)) what happen if i commmment this out? 8/14
#
#
#     #########################################選択されたバリエーションとその他メタ情報を持ってDBにサンプリングを問い合わせ + メタ情報に紐づくサロゲートモデルを取得する 6/20
#     if 'df_sampling' not in st.session_state or st.session_state.df_sampling is None:
#         print('process cost')
#         df_sampling = get_sampling(project_ids, phase_ids)
#         print('got sampling')
#         print(start - time.time(), 'sec')
#         #Excelサンプリングデータ非表示のため　フラグを設ける
#         df_sampling['from_excel'] = 1
#         if df_sampling is None:
#             st.error('このプロジェクトにはサンプリング情報が登録されていません。')
#             return
#
#         df_cost = get_cost(project_ids)#複数プロジェクトに対応させた7/4
#         print('got cost')
#         print(start - time.time(), 'sec')
#         if len(df_cost)==0:
#             st.error('このプロジェクトにはコスト情報が登録されていません。')
#             return
#         #df_costにプロジェクト情報くっつけたい
#         list_project_info_str_wo_phase = [row['project_code'] + '_' + row['z_destination'] + '_' + row['z_drive_system'] + '_' + row['architecturename'] for i, row in project_info.iterrows()]
#         project_info['project_info_str_wo_phase'] = pd.DataFrame(list_project_info_str_wo_phase)
#         df_cost = pd.merge(df_cost, project_info[['project_id','project_info_str_wo_phase']], on='project_id' )
#         #サンプリングデータでコスト情報をみることはほぼないので、process_costやらないいようにする
#         # df_base = df_sampling.loc[df_sampling['<ID>']==base_id]
#         # df_sampling = process_cost(df_sampling, df_cost, df_base)
#
#
#         rsm = Rsm()
#         df_surrogate_model_view = rsm.get_rsm(project_ids, phase_ids) #Projectに紐づいているサロゲートモデルの情報を入手する
#         print('got rsm')
#         print(start - time.time(), 'sec')
#         if len(df_surrogate_model_view)==0:
#             st.error('このプロジェクトにはサロゲートモデルが登録されていません。')
#             return
#
#         st.session_state.df_sampling =df_sampling
#         st.session_state.df_cost = df_cost
#         # st.session_state.rsm_file_path = rsm_file_path この情報はRSMインスタンスの中に入っているから必要ない
#         # st.session_state.rsm_macro = rsm_macroこの情報はRSMインスタンスの中に入っているから必要ない
#         # st.session_state.df_base = df_base
#         st.session_state.rsm = rsm
#     else:
#         print('skip process cost')
#         df_sampling = st.session_state.df_sampling
#         df_cost = st.session_state.df_cost
#         # df_base = st.session_state.df_base
#         rsm = st.session_state.rsm
#
#     ###########################################################サンプリング表示機能にシナリオリストとの連携機能を付ける
#
#     df_sampling, df_list_studies, df_study_with_model_parameter, list_studies_to_plot = add_senario_list_to_sampling(df_sampling)
#
#     print('added sim data to sampling')
#     print(start - time.time(), 'sec')
#
#
#
#     ###########################################タブ
#     ##サンプリング結果を別タブに分割する
#     Jcurb_page_id = Jcurb_tab()
#     print('tab setted')
#     print(start - time.time(), 'sec')
#     df_line_plot = None
#     settingcol1, settingcol2 = st.columns([1,1])
#     xy_expander = None
#     col1, col2, col3,_ , col4, col5,col6 = st.columns([1,1,1,1,2,4,1])
#     if Jcurb_page_id=='3':
#         ##################################################################プロットのためX軸、Y軸情報を入力させる
#         with settingcol1:
#             flag_senario_toggle, flag_sampling_display, sampling_columns, X_default_option_index, Y_default_option_index, X_axis, Y_axis, Cost_axis, X_or_Y_and_Cost, X_target, X_condition, Y_condition, list_studies_to_plot, df_line_plot = XY_settings(df_sampling, df_list_studies, list_studies_to_plot, df_study_with_model_parameter)
#
#         print('XYUI setted')
#         print(start - time.time(), 'sec')
#
#         #######ゆーざー入力情報が変わったとき、パレート解の更新を行う
#         if (X_axis != st.session_state.X_axis_before or Y_axis != st.session_state.Y_axis_before or X_condition != st.session_state.X_condition_before or Y_condition != st.session_state.Y_condition_before or X_target != st.session_state.X_target_before):#or Y_target != st.session_state.Y_target_before or X_or_Y_and_Cost != st.session_state.X_or_Y_and_Cost:
#             print('mark_parete')
#
#             #パレート解をハイライトする機能
#             df_sampling = mark_pareto(df_sampling, X_axis, X_condition, Y_axis, Y_condition) #df_base は必要ないので削除
#             print('marked pareto')
#             print(start - time.time(), 'sec')
#
#             #要求値を入力させ、ギリ満足するパレート解にフラグを立てる
#             if X_target is not None and X_target != '':
#                 df_sampling = mark_satisfied(df_sampling, X_axis, X_condition, X_target, Y_axis, Y_condition)
#
#             #jカーブ表示では性能軸を変化率に変更するため、変化率を計算した列をよういする 結局絶対値表記することになったので無効か
#             #基点はindex=0とみなす
#             # base_X_or_Y_value = df_sampling[df_sampling['<ID>']==0][X_or_Y_and_Cost]
#             # df_sampling[X_or_Y_and_Cost + '_percent'] = (df_sampling[X_or_Y_and_Cost].astype(float)/float(base_X_or_Y_value)-1)*100
#             #以上の処理で行ったユーザー設定はページ更新ごとに比較するため保存する
#             st.session_state.X_axis_before = X_axis
#             st.session_state.Y_axis_before = Y_axis
#             st.session_state.X_condition_before = X_condition
#             st.session_state.Y_condition_before = Y_condition
#             st.session_state.X_target_before = X_target
#             st.session_state.X_or_Y_and_Cost = X_or_Y_and_Cost
#             # st.session_state.Y_target_before = Y_target
#             st.session_state.df_sampling_before = df_sampling
#         else:
#             print('skip mark_parete')
#             X_axis = st.session_state.X_axis_before
#             Y_axis = st.session_state.Y_axis_before
#             X_condition = st.session_state.X_condition_before
#             Y_condition = st.session_state.Y_condition_before
#             X_target = st.session_state.X_target_before
#             # Y_target = st.session_state.Y_target_before
#             df_sampling = st.session_state.df_sampling_before
#             X_or_Y_and_Cost = st.session_state.X_or_Y_and_Cost
#
#
#     if Jcurb_page_id=='1' or Jcurb_page_id=='3':
#         with settingcol2:
#             study_id_plot_on_Jcurb, fix_cost, target_cost = Jcurb_setting(list_project_info_str, list_studies_to_plot)
#
#         print(' Jcurve UI setted')
#         print(start - time.time(), 'sec')
#
#     ##################################################################プロット
#     plotter = Plotter()
#     df_sampling_filtered = None
#     ##Jカーブプロットを別ページに分割するため、こっちではカラムを一つ消す
#     graphcol1, graphcol2, graphcol3 = st.columns([4,4, 3])
#     if Jcurb_page_id=='3':
#         #####  excel_sampling フラグによって消す
#         if not flag_sampling_display:
#             df_sampling = df_sampling[df_sampling['from_excel']!=1]
#         if not flag_senario_toggle:
#             df_sampling = df_sampling[df_sampling['from_excel']!=0] #シナリオ連携をOFFにした場合、サンプリングデータはExcelからのものだけを表示する
#         if len(df_sampling) == 0:
#             st.error('表示対象のプロットがありません。Sim管理表の仕様を選択するか、サンプリング表示をONにしてください。')
#             return
#         with graphcol3:
#             selected_inputs, df_estimated_plot, flag_SiC, df_sampling_filtered, default_slider_col = const_and_sliders(rsm, df_sampling, flag_senario_toggle, list_studies_to_plot, project_ids, phase_ids)
#             print('estimate plot setted')
#             print(start - time.time(), 'sec')
#
#
#         ##################################################################各コストアイテムごとに、基点へ組み合わせたときの出力変数をRSMで求める
#     if Jcurb_page_id=='1' or Jcurb_page_id=='3':
#         #この処理は基本df_costさえ変わらなければ再実行必用なし
#         # df_base をサロゲートモデルの出力にする
#         #add_cost_performance_infoは、入力変数を受け取って、コストアイテムごとにサロゲートモデルの出力を計算するだけなので、Siフラグけいさんも必要
#         if not 'df_cost_performance' in st.session_state or st.session_state.df_cost_performance is None or 'selected_surrogate_inputs' not in st.session_state or st.session_state.selected_surrogate_inputs != selected_inputs :
#             # st.write('recalc Jcurb')
#             df_cost_performance = rsm.add_cost_performance_info(df_cost, df_estimated_plot, project_info)#複数プロジェクトのコストに対応させる7/4 TODO　電費であっても対応できるようにする　
#             print('add_cost_performance_info done')
#             print(start - time.time(), 'sec')
#             st.session_state.df_cost_performance = df_cost_performance.copy()
#         else:
#             df_cost_performance = st.session_state.df_cost_performance.copy()       ###### RSMOutputの結果に差し替える
#
#
#
#
#
#     X_range = None
#     Y_range = None
#     accumulate_performance_range = None
#     accumulate_cost_range = None
#
#
#     if Jcurb_page_id=='1' or Jcurb_page_id=='3':
#         if 5 in rsm.get_df_surrogate_model_view()['input_surrogate_model_parameter_id'].tolist():#5:サロゲートモデルパラメータのBattセル数に相当
#             df_cost_performance['accumulate_cost'] = df_cost_performance['accumulate_cost'] - (96-selected_inputs['Battセル数'])*625 #Battセル分値下げ　TODO　コストテーブのリレーションをとる
#
#         ###SiトグルによってSiを表示する機能
#         if not flag_SiC:
#
#             df_cost_performance['estimated_燃費'] = df_cost_performance['estimated_燃費'] - 0.5 #SiCの時はサロゲートモデルの燃費を0.5下げる TODO　コストテーブのリレーションをとる
#
#             df_cost_performance['accumulate_cost'] = df_cost_performance['accumulate_cost'] - 30000 #SiCの時はコストを30000円下げる/ TODO　コストテーブのリレーションをとる
#
#         df_cost_performance['accumulate_cost_with_fix'] = df_cost_performance['accumulate_cost'] + float(fix_cost)
#
#         # JカーブにStudyのプロットを追加 TODO 今は一つのStudyしか追加対応させていない、
#         df_sampling_plot_on_Jcurb = df_sampling_filtered[df_sampling_filtered['flag_pareto']==study_id_plot_on_Jcurb[0]]
#         df_sampling_plot_on_Jcurb['estimated_燃費'] = df_sampling_plot_on_Jcurb['燃費'].tolist()[0]
#         df_sampling_plot_on_Jcurb['legend'] = study_id_plot_on_Jcurb[0]
#         #1行目はサロゲートモデルの出力なので、凡例名を変更する
#         df_cost_performance['legend'] = 'with_items'
#         df_cost_performance.loc[0,'legend'] = 'surrogate_estimated'
#         df_cost_performance = pd.concat([df_cost_performance, df_sampling_plot_on_Jcurb], ignore_index=True)
#
#
#         #二つの燃費軸のスケー統一する
#
#         accumulate_performance_range = get_preferable_range(df_cost_performance['estimated_燃費'])
#         accumulate_cost_range =  get_preferable_range(df_cost_performance['accumulate_cost_with_fix'], target_cost=float(target_cost), fix_cost= float(fix_cost))
#         if df_sampling_filtered is not None:
#             df_sampling_filtered = pd.concat([df_sampling_filtered, df_estimated_plot])
#             X_range = get_preferable_range(df_sampling_filtered[X_axis])
#             Y_range = get_preferable_range(df_sampling_filtered[Y_axis])
#         # else:
#         #     df_sampling = pd.concat([df_sampling, df_estimated_plot])
#         #     X_range = get_preferable_range(df_sampling[X_axis])
#         #     Y_range = get_preferable_range(df_sampling[Y_axis])
#
#         if Y_axis == '燃費':
#             # st.write('fueled')
#             Y_range = [min(Y_range[0], accumulate_performance_range[0]), max(Y_range[1], accumulate_performance_range[1])]
#             accumulate_performance_range = Y_range
#
#
#         with graphcol2:
#             #ユーザー選択によって表示するJカーブを変える
#             # df_cost_performance = df_cost_performance[df_cost_performance['project_id'].isin(project_info[project_info_visible]['project_id'].tolist())] TODO temporaly disable
#             with st.container():
#                 graphcol2_1, graphcol2_2 = st.columns([1,1])
#                 with graphcol2_1:
#                     st.subheader('各コストアイテムのJカーブ')
#                 with graphcol2_2:
#                     flag_from_zero_yen = st.toggle('コスト全体表示')
#                 if flag_from_zero_yen:
#                     accumulate_cost_range = [0, accumulate_cost_range[1]+accumulate_cost_range[1]*0.1] #コスト全体表示の時は0から始まるようにする
#                 event_Jcurb = plotter.plot_Jcurb(df_cost_performance,'estimated_燃費','accumulate_cost_with_fix',accumulate_performance_range,accumulate_cost_range, target_cost, float(fix_cost), study_id_plot_on_Jcurb[0]) #コスト目標値表示機能も持たせる 固定表示機能も持た8/19
#             print('Jcurb plot done')
#             print(start - time.time(), 'sec')
#
#         df_selected = None
#         df_sampling_filtered = handle_event_Jcurb(event_Jcurb, df_cost_performance, df_sampling_filtered, default_slider_col)
#
#         st.session_state.selected_surrogate_inputs = selected_inputs
#
#         #####　X＆Yの描写
#         with graphcol1:
#             st.subheader("X & Y")
#             if df_sampling_filtered is not None:
#                 event_XY = plotter.plot_scatter(df_sampling_filtered[:], X_axis, Y_axis, X_range, Y_range, list_studies_to_plot, df_line_plot)#制約線表示機能つける
#             # else:
#             #     event_XY = plotter.plot_scatter(df_sampling[:], X_axis, Y_axis, X_range, Y_range, list_studies_to_plot, df_line_plot)#せいやくせんひょうじきのうを付ける
#             print('XY plot done')
#             print(start - time.time(), 'sec')
#
#     elif Jcurb_page_id=='2':#cost chart i cant type japanese whf
#         if(st.session_state.df_cost_updated is None):
#             st.session_state.df_cost_updated = df_cost.copy()
#             st.session_state.df_cost_updated['selected'] = False
#             st.session_state.df_cost_updated['project_id_original'] =st.session_state.df_cost_updated['project_id']
#             st.session_state.df_cost_updated['id_original'] =st.session_state.df_cost_updated['id']
#             st.session_state.df_cost_updated['surrogate_model_parameter_id_original'] =st.session_state.df_cost_updated['surrogate_model_parameter_id']
#             st.session_state.df_cost_updated['project_cost_item_contradiction'] = False
#             st.session_state.df_cost_updated['project_cost_item_effect_contradiction'] = False
#
#         #get list of items so that user can select that
#         df_cost_item = sql.get_cost_item()
#         #get project_name:id map
#
#
#         #put update button
#         col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,0.5,0.5,0.5])
#         with col4:
#             flag_update_cost_info = st.button('Prjコスト情報更新', help='チェックを入れた行について、コスト情報を更新します。')
#         with col5:
#             flag_add_new_row = st.button('Prjコスト情報追加', help='プロジェクトに対するコスト情報を新規に追加します。')
#         with col6:
#             flag_delete_cost_info = st.button('Prjコスト情報削除', help='チェックを入れた行について、コスト情報を削除します。')
#
#         if flag_add_new_row:
#             st.session_state.df_cost_updated.loc[len(st.session_state.df_cost_updated)] = [None] * len(st.session_state.df_cost_updated.columns)
#             st.session_state.df_cost_updated.loc[len(st.session_state.df_cost_updated)-1]['project_cost_item_contradiction'] = False
#             st.session_state.df_cost_updated.loc[len(st.session_state.df_cost_updated)-1]['project_cost_item_effect_contradiction'] = False
#
#         #i might supposed to just give up at that point but im stupid enough not to
#         # st.session_state.df_cost_updated.loc[len(st.session_state.df_cost_updated)] = [None] * len(st.session_state.df_cost_updated.columns)
#         # st.session_state.df_cost_updated.loc[len(st.session_state.df_cost_updated)-1, 'project_info_str_wo_phase'] = '+'
#         #NONE OF THESE WORK
#
#         #render cost grid
#         # go = go_cost(df_cost.copy()[['project_info_str_wo_phase', 'project_id']].drop_duplicates())
#         # ag_cost = AgGrid(st.session_state.df_cost_updated,
#         #                  go,
#         #                  height = 801,
#         #                  allow_unsafe_jscode=True,
#         #                  custom_css=css_ag,
#         #                  fit_columns_on_grid_load=True,
#         #                  update_mode=GridUpdateMode.VALUE_CHANGED,
#
#         #                  )
#         # st.session_state.df_cost_edited = ag_cost['data']
#         cost_grid(df_cost.copy()[['project_info_str_wo_phase', 'project_id']].drop_duplicates())
#         # st.session_state.st.session_state.df_cost_updated = st.session_state.df_cost_updated.copy()
#         if flag_update_cost_info:
#             #データ矛盾を警告する
#             df_project_cost_item_contradiction = st.session_state.df_cost_edited[st.session_state.df_cost_edited['project_cost_item_contradiction']]
#             if len(df_project_cost_item_contradiction)>=1:
#                     df_project_cost_item_contradiction = df_project_cost_item_contradiction.iloc[0]
#                     project = df_project_cost_item_contradiction['project_info_str_wo_phase']
#                     item = df_project_cost_item_contradiction['part_name']
#                     st.error('プロジェクト：'+project+'のアイテム：'+item+'は、単価、もしくはレート名が一致していません。各行で入力内容を一致させてください。')
#                     return
#             df_project_cost_item_effect_contradiction = st.session_state.df_cost_edited[st.session_state.df_cost_edited['project_cost_item_effect_contradiction']]
#             if len(df_project_cost_item_effect_contradiction)>=1:
#                     df_project_cost_item_effect_contradiction = df_project_cost_item_effect_contradiction.iloc[0]
#                     project = df_project_cost_item_effect_contradiction['project_info_str_wo_phase']
#                     item = df_project_cost_item_effect_contradiction['part_name']
#                     category = df_project_cost_item_effect_contradiction['parameter_name']
#                     st.error('プロジェクト：'+project+'のアイテム：'+item+'は、カテゴリ：'+category+'に対して二行以上存在しています。行を一行のみにしてください。')
#                     return
#
#             dia.update_cost_info(st.session_state.df_cost_edited)
#
#         if flag_delete_cost_info:
#             dia.delete_cost_info(st.session_state.df_cost_edited)
#
#     elif Jcurb_page_id == '4':
#         st.session_state.df_cost_item =sql.get_cost_item()
#         #put update button
#         col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,0.5,0.5,0.5])
#         with col4:
#             flag_update_cost_info = st.button('コストアイテム情報更新', help='チェックを入れた行について、コストアイテム情報を更新します。')
#         with col5:
#             flag_add_new_row = st.button('コストアイテム情報追加', help='コストアイテム情報を新規に追加します。')
#         with col6:
#             flag_delete_cost_info = st.button('コストアイテム情報削除', help='チェックを入れた行について、コストアイテム情報を削除します。')
#
#
#
#     if 'Jcurb_page_id' not in st.session_state or Jcurb_page_id != st.session_state.Jcurb_page_id:
#         st.session_state.Jcurb_page_id = Jcurb_page_id
#
#
# # @st.fragment
# def cost_grid( df_id_project):
#     go = go_cost(df_id_project)
#     ag_cost = AgGrid(st.session_state.df_cost_updated,
#                      go,
#                      height = 801,
#                      allow_unsafe_jscode=True,
#                      custom_css=css_ag,
#                      fit_columns_on_grid_load=True,
#                      update_mode=GridUpdateMode.VALUE_CHANGED,
#
#                      )
#     st.session_state.df_cost_edited = ag_cost['data']
#
# @st.fragment
# def cost_item_grid():
#     go = go_cost_item()#直近こっちではなくない？
#     ag_cost_item = AgGrid(st.session_state.df_cost_item,
#                           go,
#                           height = 800,
#                           allow_unsafe_jscode=True,
#                           custom_css=css_ag,
#                           fit_columns_on_grid_load=True,
#                           update_mode=GridUpdateMode.VALUE_CHANGED
#                           )
#
#     st.session_state.df_cost_item_edited
#
#
# def go_cost(df_id_project):
#     #get list of cost_rate so that user can select rates from list
#     df_cost_rate = sql.get_cost_rate()
#     #get list of surrogate_model_parameter so that use can select categories form list
#     df_surrogate_model_parameter = sql.get_surrogate_model_parameter()
#     df_surrogate_model_parameter = sql.get_surrogate_model_parameter()
#     #get list of items so that user can select that
#     df_cost_item = sql.get_cost_item()
#     df_id_project = df_id_project #the worst line of code ever but its necessary
#     #get project_name:id map
#
#     #コストレート用マップ
#     cost_rate_id_map = dict(zip(df_cost_rate['rate_name'], df_cost_rate['id']))
#     cost_rate_map = dict(zip(df_cost_rate['rate_name'], df_cost_rate['rate']))
#     cost_rate_unit_map = dict(zip(df_cost_rate['rate_name'], df_cost_rate['unit']))
#     #コストアイテム用マップ
#     cost_item_id_map = dict(zip(df_cost_item['item_name_4'], df_cost_item['id']))
#     cost_item_1_map = dict(zip(df_cost_item['item_name_4'], df_cost_item['item_name_1']))
#     cost_item_2_map = dict(zip(df_cost_item['item_name_4'], df_cost_item['item_name_2']))
#     cost_item_3_map = dict(zip(df_cost_item['item_name_4'], df_cost_item['item_name_3']))
#     #サロゲートモデルパラメータ用マップj
#     surrogate_model_parameter_id_map = dict(zip(df_surrogate_model_parameter['parameter_name'], df_surrogate_model_parameter['id']))
#     #プロジェクト情報用まっぷ
#     id_project_map = dict(zip(df_id_project['project_info_str_wo_phase'], df_id_project['project_id']))
#
#     js_cost_rate_id_map = str(cost_rate_id_map).replace("'", '"')
#     js_cost_rate_map = str(cost_rate_map).replace("'", '"')
#     js_cost_rate_unit_map = str(cost_rate_unit_map).replace("'", '"')
#     js_cost_item_id_map = str(cost_item_id_map).replace("'", '"')
#     js_cost_item_1_map = str(cost_item_1_map).replace("'", '"')
#     js_cost_item_2_map = str(cost_item_2_map).replace("'", '"')
#     js_cost_item_3_map = str(cost_item_3_map).replace("'", '"')
#     js_surrogate_model_parameter_id_map = str(surrogate_model_parameter_id_map).replace("'", '"')
#     js_id_project_map = str(id_project_map).replace("'", '"')
#
#     #project_info_str_wo_phaseクリック時コールバック
#     callback_project_info = JsCode(f"""
#                 function (params){{
#                     const id_project_mapping = {js_id_project_map};
#                     const sourceValue = params.newValue;
#                     const id_mappedValue = id_project_mapping[sourceValue] || null;
#                     params.data["project_id"] = id_mappedValue;
#
#                 }}
#
#                  """)
#     #project_info_str_wo_phaseクリック時行追加ールバック
#     callback_project_info_add_row = JsCode(f"""
#                 function (params){{
#                     console.log(params);
#                     if (params.value == '+'){{
#                         console.log("add row");
#                         const newRow = {{}};
#                         params.api.getAllGridColumns().forEach(col => {{
#                             newRow[col.getColDef().field] = null;
#                         }});
#                         console.log(newRow);
#                         const res = params.api.applyTransaction({{ add: [newRow]}});
#                         res.add[0].id = res.add[0].rowIndex;
#                         const res2 = params.api.applyTransaction({{ update: [res.add[0]]}});
#                         console.log(res);
#                         console.log(res2);
#
#
#                     }}
#                 }}
#
#     """)
#
#     #レート名変更時の自動書き換えコールバック
#     callback_rate_name = JsCode(f"""
#                 function (params){{
#                     const id_mapping = {js_cost_rate_id_map};
#                     const rate_mapping = {js_cost_rate_map};
#                     const unit_mapping = {js_cost_rate_unit_map};
#                     const sourceValue = params.newValue;
#                     const id_mappedValue = id_mapping[sourceValue] || null;
#                     const rate_mappedValue = rate_mapping[sourceValue] || null;
#                     const unit_mappedValue = unit_mapping[sourceValue] || null;
#
#                     params.node.setDataValue("cost_rate_id", id_mappedValue);
#                     params.node.setDataValue("cost_rate", rate_mappedValue);
#                     params.node.setDataValue("unit", unit_mappedValue);
#                 }}
#             """)
#     #アイテム名変更時の自動書き換えコールバック
#     callback_part_name = JsCode(f"""
#                 function (params){{
#                     const item_id_mapping = {js_cost_item_id_map};
#                     const item_1_mapping = {js_cost_item_1_map};
#                     const item_2_mapping = {js_cost_item_2_map};
#                     const item_3_mapping = {js_cost_item_3_map};
#                     const sourceValue = params.newValue;
#                     const item_id_mappedValue = item_id_mapping[sourceValue] || null;
#                     const item_1_mappedValue = item_1_mapping[sourceValue] || null;
#                     const item_2_mappedValue = item_2_mapping[sourceValue] || null;
#                     const item_3_mappedValue = item_3_mapping[sourceValue] || null;
#
#                     params.node.setDataValue("id", item_id_mappedValue);
#                     params.node.setDataValue("item_name_1", item_1_mappedValue);
#                     params.node.setDataValue("item_name_2", item_2_mappedValue);
#                     params.node.setDataValue("item_name_3", item_3_mappedValue);
#
#                 }}
#             """)
#     #サロゲートモデルパラメータ名書き換えコールバック
#     callback_surrogate_model_parameter_name = JsCode(f"""
#                 function (params){{
#                     const surrogate_model_parameter_id_mapping = {js_surrogate_model_parameter_id_map};
#                     const sourceValue = params.newValue;
#                     const id_mappedValue = surrogate_model_parameter_id_mapping[sourceValue] || null;
#                     params.node.setDataValue("surrogate_model_parameter_id", id_mappedValue);
#
#                 }}
#
#                  """)
#
#     #どこでも列を編集したらその行の円をUpdateするコールバック
#     callback_calc_cost_jpy = JsCode(f"""
#                 function (params){{
#                     console.log(params);
#                     if (params.colDef.field != 'selected'){{
#                         params.node.setDataValue("cost_change_amount",params.data["cost_rate"] * params.data["original_cost"]);
#                         params.node.setDataValue("selected", true);
#                         params.api.refreshCells({{columns: ["original_cost", "parameter_change_amount"], rowNodes:[params.node], force: true}});
#                     }}
#                 }}
#
#                                     """)
#
#     #コスト情報の不一致を知らせるコールバック
#     cellStyle_project_cost_item_contradiction =JsCode(f"""
#                 function (params){{
#                     console.log(params);
#                     const current = params.data;
#                     const api = params.api;
#                     const rowCount = api.getDisplayedRowCount();
#                     let values = [];
#                     let cost_rates = [];
#
#                     for (let i = 0; i < rowCount; i++){{
#                         let row = api.getDisplayedRowAtIndex(i).data;
#                         if (row.project_id === current.project_id &&
#                             row.id === current.id) {{
#                             values.push(row.original_cost);
#                             cost_rates.push(row.cost_rate_id)
#                             }}
#                     }}
#                     let uniqueValues = [...new Set(values)];
#                     let uniqueCostRates = [...new Set(cost_rates)];
#                     if (uniqueValues.length > 1 || uniqueCostRates.length > 1){{
#                         params.node.setDataValue("project_cost_item_contradiction", true);
#                         return {{backgroundColor: "red" }};
#                     }}
#                     params.node.setDataValue("project_cost_item_contradiction", false);
#                     return {{'background-color':'#FFFFCC'}};
#                 }}
#     """)
#     #パラメータ情報の不一致を知らせるコールバック
#
#     cellStyle_project_cost_item_effect_contradiction =JsCode(f"""
#                 function (params){{
#                     const current = params.data;
#                     const api = params.api;
#                     const rowCount = api.getDisplayedRowCount();
#                     let matchCount = 0;
#
#                     for (let i = 0; i < rowCount; i++){{
#                         let row = api.getDisplayedRowAtIndex(i).data;
#                         if (row.project_id === current.project_id &&
#                             row.id === current.id &&
#                             row.surrogate_model_parameter_id === current.surrogate_model_parameter_id) {{
#                             matchCount += 1;
#                             }}
#                     }}
#                     if (matchCount > 1){{
#                         params.node.setDataValue("project_cost_item_effect_contradiction", true);
#                         return {{backgroundColor: "red" }};
#                     }}
#                     params.node.setDataValue("project_cost_item_effect_contradiction", false);
#                     return {{'background-color':'#FFFFCC'}};
#                 }}
#     """)
#
#     go = {
#         'columnDefs':[
#             {
#                 'headerName':'選択',
#                 'field':'selected',
#                 'editable': True,
#                 'cellStyle':{
#                     'background-color':'#FFFFCC'
#                 }
#             },
#             {
#                 'headerName':'プロジェクト',
#                 'field':'project_info_str_wo_phase',
#                 'editable': True,
#                 'cellStyle':{
#                     'background-color':'#FFFFCC'
#                 },
#                 'cellEditor': 'agSelectCellEditor',
#                 'cellEditorParams': {
#                     'values': df_id_project['project_info_str_wo_phase'].tolist()
#                     },
#                 'onCellValueChanged': callback_project_info
#             },
#             {
#                 'headerName':'大分類',
#                 'field':'item_name_1'
#             },
#             {
#                 'headerName':'中分類',
#                 'field':'item_name_2'
#             },
#             {
#                 'headerName':'小分類',
#                 'field':'item_name_3'
#             },
#             {
#                 'headerName':'アイテム',
#                 'field':'part_name',
#                 'editable': True,
#                 'cellStyle':{
#                     'background-color':'#FFFFCC'
#                 },
#                 'cellEditor': 'agSelectCellEditor',
#                 'cellEditorParams': {
#                     'values': df_cost_item['item_name_4'].tolist()
#                     },
#
#                 'onCellValueChanged': callback_part_name
#             },
#             {
#                 'headerName':'単価[JPY]',
#                 'field':'cost_change_amount'
#             },
#             {
#                 'headerName':'単価',
#                 'field':'original_cost',
#                 'editable': True,
#                 'cellStyle':cellStyle_project_cost_item_contradiction
#             },
#             {
#                 'headerName':'レートID',
#                 'field':'cost_rate_id'
#             },
#             {
#                 'headerName':'換算レート',
#                 'field':'cost_rate'
#             },
#             {
#                 'headerName':'レート名',
#                 'field':'cost_rate_name',
#                 'editable': True,
#                 'cellStyle':{
#                     'background-color':'#FFFFCC'
#                 },
#                 'cellEditor': 'agSelectCellEditor',
#                 'cellEditorParams': {
#                     'values': df_cost_rate['rate_name'].tolist()
#                     },
#
#                 'onCellValueChanged': callback_rate_name
#             },
#             {
#                 'headerName':'効果',
#                 'field':'parameter_change_amount',
#
#                 'cellStyle':cellStyle_project_cost_item_effect_contradiction,
#                 'editable': True,
#             },
#             {
#                 'headerName':'カテゴリ',
#                 'field':'parameter_name',
#                 'editable': True,
#                 'cellStyle':{
#                     'background-color':'#FFFFCC'
#                 },
#                 'cellEditor': 'agSelectCellEditor',
#                 'cellEditorParams': {
#                     'values': df_surrogate_model_parameter['parameter_name'].tolist()
#                     },
#                 'onCellValueChanged': callback_surrogate_model_parameter_name
#
#             },
#             {
#                 'field':'project_id',
#                 'hide':True
#             },
#             {
#                 'field':'project_id_original',
#                 'hide':True
#             },
#             {
#                 'field':'id',
#                 'hide':True
#             },
#             {
#                 'field':'id_original',
#                 'hide':True
#             },
#             {
#                 'field':'unit',
#                 'hide':True
#             },
#             {
#                 'field':'surrogate_model_parameter_id',
#                 'hide':False
#             },
#             {
#                 'field':'surrogate_model_parameter_id_original',
#                 'hide':True
#             },
#             {
#                 'field':'project_cost_item_contradiction',
#                 'hide':False
#             },
#             {
#                 'field':'project_cost_item_effect_contradiction',
#                 'hide':False
#             },
#
#         ],
#         'defaultColDef':{
#             'resizable': True,
#             'headerClass': 'cost'
#         },
#         'onCellValueChanged': callback_calc_cost_jpy, #どこかの値が変更されたときに動くJS関数
#         'suppressContextMenu': False, #このグリッド上ではChrome右クリックメニューを開かない
#
#     #     'getContextMenuItems': [
#     #     {
#     #         "name": "Insert Blank Row",
#     #         "action": """
#     #             function(){
#     #                 const newRow = {};
#     #                 params.columnApi.getAllColumns().forEach(col => {
#     #                     newRow[col.getColDef().field] = null;
#     #                 });
#     #                 gridOptions.api.applyTransaction({ add: [newRow]});
#     #             }
#     #         """
#     #     },
#     #     "copy",
#     #     "csvExport"
#     # ]
#     }
#     return go
#
#
# if __name__ == "__main__":
#     Jcurb_ui()

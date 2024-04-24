import pandas as pd
import numpy as np
import logging
import streamlit as st
import plotly.graph_objects as go


class OutlierDetector:
    def __init__(self, data):
        self.data = data
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        
        
    def outlier_detect_IQR(self, data, col, threshold=0.05):
        try:
            Q1 = np.percentile(data[col], 25)
            Q3 = np.percentile(data[col], 75)
            IQR = Q3 - Q1
            upper_fence = Q3 + 1.5 * IQR
            lower_fence = Q1 - 1.5 * IQR
            para = (upper_fence, lower_fence)
            outlier_index = data[(data[col] > upper_fence) | (data[col] < lower_fence)].index
            num_outliers = len(outlier_index)
            prop_outliers = num_outliers / len(data)
            st.write('Num of outlier detected:', num_outliers)
            st.write('Proportion of outlier detected:', prop_outliers)
            
            # Check if the proportion of outliers exceeds the threshold
            if prop_outliers > threshold:
                raise ValueError(f"Proportion of outliers ({prop_outliers:.2%}) exceeds the threshold ({threshold:.2%})")

            # Plotting
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data[col],
                                    mode='markers',
                                    name='Data'))
            fig.add_trace(go.Scatter(x=outlier_index, y=data.loc[outlier_index, col],
                            mode='markers',
                            marker=dict(color='red', size=8),
                            name='Outliers'))

            fig.update_layout(title='Outlier Detection',
                            xaxis_title='Index',
                            yaxis_title=col)
            st.plotly_chart(fig)

            return outlier_index, para
        except Exception as e:
            self.logger.error("An error occurred while detecting outliers: %s", str(e))
            raise

    def outlier_detect_mean_std(self, data, col, threshold=3):
        try:
            upper_fence = data[col].mean() + threshold * data[col].std()
            lower_fence = data[col].mean() - threshold * data[col].std()
            para = (upper_fence, lower_fence)
            outlier_index = data[(data[col] > upper_fence) | (data[col] < lower_fence)].index
            num_outliers = len(outlier_index)
            prop_outliers = num_outliers / len(data)
            st.write('Num of outlier detected:', num_outliers)
            st.write('Proportion of outlier detected:', prop_outliers)
            
            # Plotting
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data[col],
                                     mode='markers',
                                     name='Data'))
            fig.add_trace(go.Scatter(x=outlier_index, y=data.loc[outlier_index, col],
                            mode='markers',
                            marker=dict(color='red', size=8),
                            name='Outliers'))
            fig.update_layout(title='Outlier Detection',
                              xaxis_title='Index',
                              yaxis_title=col)
            st.plotly_chart(fig)
            
            
            return outlier_index, para
        except Exception as e:
            self.logger.error("An error occurred while detecting outliers: %s", str(e))
            raise

    def outlier_detect_MAD(self, data, col, threshold=3.5):
        try:
            median = data[col].median()
            median_absolute_deviation = np.median([np.abs(y - median) for y in data[col]])
            modified_z_scores = pd.Series([0.6745 * (y - median) / median_absolute_deviation for y in data[col]])
            outlier_index = data.index[np.abs(modified_z_scores) > threshold]
            
            print('Num of outlier detected:', len(outlier_index))
            print('Proportion of outlier detected:', len(outlier_index) / len(data))
            
            # Plotting
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data[col],
                                    mode='markers',
                                    name='Data'))
            fig.add_trace(go.Scatter(x=outlier_index, y=data.loc[outlier_index, col],
                            mode='markers',
                            marker=dict(color='red', size=8),
                            name='Outliers'))

            fig.update_layout(title='Outlier Detection',
                            xaxis_title='Index',
                            yaxis_title=col)
            st.plotly_chart(fig)

            return outlier_index
        except Exception as e:
            self.logger.error("An error occurred while detecting outliers: %s", str(e))
            raise

    def impute_outlier_with_arbitrary(self, data, outlier_index, value, col):
        try:
            data_copy = data
            imputed_indices = []
            for column in col:
                data_copy.loc[outlier_index, column] = value
                imputed_indices.extend(data_copy[outlier_index].index)
            return data_copy, imputed_indices
        except KeyError as e:
            self.logger.error(f"Column not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred while imputing outliers: {e}")
            raise


    def windsorization(self, data, col, para, strategy='both'):
        try:
            data_copy = data
            if strategy == 'both':
                data_copy.loc[data_copy[col] > para[0], col] = para[0]
                data_copy.loc[data_copy[col] < para[1], col] = para[1]
            elif strategy == 'top':
                data_copy.loc[data_copy[col] > para[0], col] = para[0]
            elif strategy == 'bottom':
                data_copy.loc[data_copy[col] < para[1], col] = para[1]
            return data_copy
        except Exception as e:
            self.logger.error("An error occurred while performing windsorization: %s", str(e))
            raise

    def drop_outlier(self, data, outlier_index):
        try:
            data_copy = data.loc[~data.index.isin(outlier_index)]
            return data_copy
        except Exception as e:
            self.logger.error("An error occurred while dropping outliers: %s", str(e))
            raise


    def impute_outlier_with_avg(self, data, col, outlier_index, strategy='mean'):
        try:
            data_copy = data
            impute_value = None
            if strategy == 'mean':
                impute_value = data_copy[col].mean()
            elif strategy == 'median':
                impute_value = data_copy[col].median()
            elif strategy == 'mode':
                impute_value = data_copy[col].mode()[0]

            if isinstance(outlier_index, pd.Index) and outlier_index.isin(data_copy.index).all():
                data_copy.loc[outlier_index, col] = impute_value
            else:
                self.logger.warning(f"Outlier index {outlier_index} is not a valid index for the DataFrame.")
            return data_copy
        except Exception as e:
            self.logger.error("An error occurred while imputing outliers with average value: %s", str(e))
            raise
    
    def outlier_detect(self):
        
        st.markdown(
            "<h1 style='text-align: center; font-size: 30px;'>Detect and Impute Outliers</h1>", 
            unsafe_allow_html=True
        )

        st.markdown("---")
        
        st.markdown("<h2 style='text-align: center; font-size: 20px;'>Dataset</h1>", unsafe_allow_html=True)
        st.dataframe(self.data, width=800)

        option = st.sidebar.selectbox("Select an Outlier Detection/Imputation Method", [
            "Detect Outliers using IQR",
            "Detect Outliers using Mean and Standard Deviation",
            "Detect Outliers using Median Absolute Deviation (MAD)",
            "Impute Outliers with Arbitrary Value",
            "Windsorize Outliers",
            "Impute Outliers with Average",
            "Drop Outliers"
        ])

        if option == "Detect Outliers using IQR":
            st.markdown("<h1 style='text-align: center; font-size: 25px;'>Detect Outliers using IQR</h1>", unsafe_allow_html=True)
            threshold = st.number_input("Threshold", min_value=0.1, value=1.5)
            col = st.selectbox("Select a column", options=self.data.columns)
            if st.button("Detect Outliers"):
                outlier_index, para = self.outlier_detect_IQR(data=self.data, col=col, threshold=threshold)
                
                st.write("Outlier indices:", outlier_index)
                st.write("Parameters:", para)

        elif option == "Detect Outliers using Mean and Standard Deviation":
            st.markdown("<h1 style='text-align: center; font-size: 25px;'>Detect Outliers using Mean and Standard Deviation</h1>", unsafe_allow_html=True)
            threshold = st.number_input("Threshold", min_value=0.1, value=3.0)
            col = st.selectbox("Select a column", options=self.data.columns)
            if st.button("Detect Outliers"):
                outlier_index, para = self.outlier_detect_mean_std(data=self.data, col=col, threshold=threshold)
               
                st.write("Outlier indices:", outlier_index)
                st.write("Parameters:", para)

        elif option == "Detect Outliers using Median Absolute Deviation (MAD)":
            st.markdown("<h1 style='text-align: center; font-size: 25px;'>Detect Outliers using Median Absolute Deviation (MAD)</h1>", unsafe_allow_html=True)
            threshold = st.number_input("Threshold", min_value=0.1, value=3.5)
            col = st.selectbox("Select a column", options=self.data.columns)
            if st.button("Detect Outliers"):
                outlier_index = self.outlier_detect_MAD(data=self.data, col=col, threshold=threshold)
                
                st.write("Outlier indices:", outlier_index)

        elif option == "Impute Outliers with Arbitrary Value":
            st.markdown("<h1 style='text-align: center; font-size: 25px;'>Impute Outliers with Arbitrary Value</h1>", unsafe_allow_html=True)
            threshold = st.number_input("Threshold", min_value=0.1, value=1.5)
            col = st.selectbox("Select a column", options=self.data.columns)
            outlier_index_value = self.outlier_detect_IQR(data=self.data, col=col, threshold=threshold)
            value = st.number_input("Enter Arbitrary Value")
            if st.button("Impute Outliers"):
                data_impute_arb = self.impute_outlier_with_arbitrary(data=self.data, outlier_index=outlier_index_value, value=value, col=col)
                st.write(data_impute_arb)

        elif option == "Windsorize Outliers":
            st.markdown("<h1 style='text-align: center; font-size: 25px;'>Windsorize Outliers</h1>", unsafe_allow_html=True)
            threshold = st.number_input("Threshold", min_value=0.1, value=1.5)
            col = st.selectbox("Select a column", options=self.data.columns)
            outlier_index_value, para = self.outlier_detect_IQR(data=self.data, col=col, threshold=threshold)
            strategy = st.selectbox("Windsorization Strategy", ['both', 'top', 'bottom'])

            if st.button("Windsorize"):
                data_windsorized = self.windsorization(data=self.data, col=col, para=para, strategy=strategy)
                st.write(data_windsorized)

                # Plotting the data after Windsorization
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data_windsorized.index, y=data_windsorized[col],
                                        mode='markers',
                                        name='Data'))
                fig.update_layout(title='Data after Windsorization',
                                xaxis_title='Index',
                                yaxis_title=col)
                st.plotly_chart(fig)

        elif option == "Impute Outliers with Average":
            st.markdown("<h1 style='text-align: center; font-size: 25px;'>Impute Outliers with Average</h1>", unsafe_allow_html=True)

            strategy = st.selectbox("Imputation Strategy", ['mean', 'median', 'mode'])

            col = st.selectbox("Select a column", options=self.data.columns)

            threshold = st.number_input("Threshold", min_value=0.1, value=1.5)

            outlier_index_value = self.outlier_detect_IQR(data=self.data, col=col, threshold=threshold)

            if st.button("Impute Outliers"):
                data_impute_avg = self.impute_outlier_with_avg(data=self.data, col=col, outlier_index=outlier_index_value, strategy=strategy)
                st.write(data_impute_avg)
        
        elif option == "Drop Outliers":
            st.markdown("<h1 style='text-align: center; font-size: 25px;'>Drop Outliers</h1>", unsafe_allow_html=True)
            threshold = st.number_input("Threshold", min_value=0.1, value=1.5)
            col = st.selectbox("Select a column", options=self.data.columns)
            outlier_index_value = self.outlier_detect_IQR(data=self.data, col=col, threshold=threshold)
            if st.button("Drop Outliers"):
                data_dropped = self.drop_outlier(data=self.data, outlier_index=outlier_index_value)
                st.write(data_dropped)

        return self.data
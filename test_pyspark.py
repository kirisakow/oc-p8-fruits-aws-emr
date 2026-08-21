from pyspark.sql import SparkSession

# Créer une session Spark
spark = SparkSession.builder \
                    .appName('TestPySpark') \
                    .config('spark.driver.extraJavaOptions', '-Dlog4j.configuration=file:log4j2.properties') \
                    .getOrCreate()

spark.sparkContext.setLogLevel('ERROR')

# Créer un DataFrame simple
data = [('Alice', 1), ('Bob', 2), ('Cathy', 3)]
df = spark.createDataFrame(data, ['Name', 'Age'])

# Afficher le DataFrame
df.show()

# Fermer la session Spark
spark.stop()

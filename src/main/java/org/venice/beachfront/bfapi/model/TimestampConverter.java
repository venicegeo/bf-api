package org.venice.beachfront.bfapi.model;

import java.sql.Timestamp;
import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

import org.joda.time.DateTime;

@Converter(autoApply = true)
public class TimestampConverter implements AttributeConverter<DateTime, Timestamp> {
    @Override
    public Timestamp convertToDatabaseColumn(DateTime dateTime) {
         if (dateTime == null) {
            return null;
         }
            return new Timestamp(dateTime.getMillis());
    }

    @Override
    public DateTime convertToEntityAttribute(Timestamp localTime) {
         if (localTime == null) {
            return null;
         }
            return new DateTime(localTime.getTime());
    }
}

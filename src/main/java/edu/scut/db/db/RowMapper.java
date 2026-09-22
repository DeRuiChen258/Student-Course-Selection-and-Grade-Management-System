package edu.scut.db.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

@FunctionalInterface
public interface RowMapper<T> {

    T map(ResultSet rs) throws SQLException;

    static <T> List<T> mapList(ResultSet rs, RowMapper<T> mapper) throws SQLException {
        List<T> list = new ArrayList<>();
        while (rs.next()) {
            list.add(mapper.map(rs));
        }
        return list;
    }
}

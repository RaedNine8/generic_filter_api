package com.example.model;
import jakarta.persistence.*;
import java.util.*;
@Entity @Table(name="authors") public class Author {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 @Column(nullable=false) private String name;
 @OneToMany(mappedBy="author") private List<Book> books=new ArrayList<>();
 public Long getId(){return id;} public String getName(){return name;} public List<Book> getBooks(){return books;}
}
